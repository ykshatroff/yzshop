"""
A dispatcher is a generalized provider of management functions.

The rationale is not to write separate view functions when they are
    mostly just copies of each other with the only difference being the model.

In order to be managed by the YzAdmin app, an application must register its
    dispatcher to the global dispatcher. The list of registered dispatchers
    is used in request dispatching as well as admin menu building, etc.
    To automate registration, a setting "yzadmin.managed_models" can be used
    to list all models (full module.class specs) subject to registration.
    Also a setting "yzadmin.managed_apps" can list
    the Django applications (modules) like `yz.catalog`, in which
    modules the dispatcher looks for a module yzadmin where custom registration
    may be performed.
"""
import logging
import re

from . import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django import forms
from django.forms.models import modelform_factory
from django import http
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _

from yz.utils import import_module
from yz.utils import import_symbol

logger = logging.getLogger("default")


class DispatcherException(Exception):
    _message = _('Generic exception')
    status_code = 500

    def __init__(self, **kwargs):
        message = self._message % kwargs
        super(DispatcherException, self).__init__(message)


class ViewNotFoundException(DispatcherException):
    """
    Exception thrown when a view is not found by name
    """
    _message = _('No such view "%(view)s"')
    status_code = 404


class ViewArgumentsException(DispatcherException):
    """
    Exception thrown when a view is not found by name
    """
    _message = 'Invalid number of arguments for view "%(view)s": given %(given)d, needed %(needed)d'
    status_code = 404


class ItemNotFoundException(DispatcherException):
    """
    Exception thrown when a view is not found by name
    """
    _message = _('No item found with %(id_field)s = "%(item_id)s"')
    status_code = 404

    def __init__(self, item_id, id_field='id'):
        # message = self.message % { 'item_id': item_id }
        super(ItemNotFoundException, self).__init__(item_id=item_id,
                                                    id_field=id_field)


class BadParameterException(DispatcherException):
    """
    Exception thrown when a parameter
    """
    _message = _('Invalid value for parameter "%(param)s"')
    status_code = 404



class Dispatcher(object):
    """
    A generic dispatcher for YZ management `console`
    Its role is to dispatch requests to model dispatchers
    """
    registered_dispatchers = {}

    menu = None

    _init_done = False

    @classmethod
    def init(cls):
        #logger.debug("Dispatcher.init()")
        if not cls._init_done:
            logger.debug("Dispatcher.init() first run")
            # create menu
            admin_menu_create_fn = import_symbol(settings.MENU)
            cls.menu = admin_menu_create_fn()
            for app in settings.MANAGED_APPS:
                #logger.debug("Dispatcher.init(%s)", app)
                yzadmin_setup = "%s.yzadmin.setup" % app
                try:
                    setup_fn = import_symbol(yzadmin_setup)
                except ImportError:
                    logger.debug("Dispatcher.init() ImportError(%s)", yzadmin_setup)
                else:
                    setup_fn(cls)
                    logger.debug("Dispatcher.init(%s) OK", app)
            cls._init_done = True

    @classmethod
    def register(cls, dispatcher, name=None, title=None, menuitem=None):
        if not name:
            name = dispatcher.name
        logger.debug("Dispatcher.register(%s)", name)
        if not title:
            title = dispatcher.title_plural or dispatcher.title
        cls.registered_dispatchers[name] = dispatcher
        if menuitem:
            cls.menu.get_item(menuitem).add(name, title)

    @classmethod
    def process(cls, request, arg):
        logger.debug("Dispatcher.process(%s)", arg)
        try:
            dispatcher_name, arg = arg.split("/", 1)
        except ValueError:
            dispatcher_name, arg = arg, ""
        if dispatcher_name not in cls.registered_dispatchers:
            raise http.Http404
        request.in_yzadmin = True
        dispatcher = cls.registered_dispatchers[dispatcher_name]
        try:
            return dispatcher.process(request, arg)
        except DispatcherException as ex:
            return dispatcher.display_error(request, ex)
        except http.Http404 as ex:
            return dispatcher.display_error(request, ex)

    @classmethod
    def get_menu(cls):
        return cls.menu

    @classmethod
    def get_model_dispatcher(cls, model):
        """
        Get the dispatcher for the specified model
        """
        try:
            model_name = model.__name__.lower()
        except AttributeError:
            model_name = model

        try:
            return self.registered_dispatchers[model_name]
        except KeyError:
            for disp in self.registered_dispatchers.values():
                if model == disp.model:
                    return disp
            raise ValueError("No dispatcher found for model '%s'" % model)


class ModelDispatcher(object):
    """
    A model dispatcher for YZ management `console`
    """
    name = None
    title = None
    title_plural = None
    model = None
    template_path = "yzadmin/%(name)s/%(action)s.html"
    add_form_class = None
    form_class = None

    MSG_SAVED = _('Item saved successfully')
    MSG_ADDED = _('Item added successfully')
    MSG_DELETED = _('Item deleted')
    MSG_UPDATED = _('Data updated')
    MSG_ERROR = _('Errors occurred')
    messages = {
        'item_saved': _('Item saved successfully'),
    }


    def __init__(self, model=None):
        """
        Create a dispatcher for a model
        """
        logger.debug("ModelDispatcher.__init__(%s)", model)
        if model is None:
            model = self.model
            if model is None:
                raise ValueError("Model not supplied")
        if not hasattr(model, 'objects'):
            raise ValueError("Model not valid")
        self.model = model
        self.name = self.name or self.model.__name__.lower()
        self.title = self.title or self.model._meta.verbose_name
        self.title_plural = self.title_plural or self.model._meta.verbose_name_plural
        self.form_class = self.form_class or modelform_factory(self.model)


    def __str__(self):
        """
        """
        return self.name


    def identify_template(self, action, is_ajax=False):
        """
        Get a list of templates for an action
        """
        if is_ajax:
            action = "%s-ajax" % action
        tpls = ( self.template_path % {'name': self.name, 'action': action},
                "yzadmin/defaults/%s.html" % action )
        return tpls


    def process(self, request, arg):
        """
        Parse arguments and
        Dispatch request to a view with args
        """
        logger.debug("ModelDispatcher.process(%s)", arg)
        if arg:
            args = arg.strip("/").split("/")
            view = args.pop(0)
        else:
            view, args = "index", []
        return self._process(request, view, *args)

    def _process(self, request, view, *args):
        try:
            func = getattr(self, "%s_view" % view)
        except AttributeError:
            raise ViewNotFoundException(view=view)

        # take into account two 'internal' arguments of a view:
        # view(self, request, *args)
        request_argcount = len(args)
        max_argcount = func.func_code.co_argcount - 2
        min_argcount = max_argcount
        if func.func_defaults:
            min_argcount -= len(func.func_defaults)
        if request_argcount > max_argcount:
            raise ViewArgumentsException(view=view, given=request_argcount,
                    needed=max_argcount)
        if request_argcount < min_argcount:
            raise ViewArgumentsException(view=view, given=request_argcount,
                    needed=min_argcount)

        return func(request, *args)


    def display_error(self, request, exception):
        """
        Show an error message in the dispatcher's environment
        kwargs are the parameters to error message
        """
        resp = self.render( 'error', request, {'error': exception} )
        resp.status_code = exception.status_code
        return resp


    def index_view(self, request):
        """
        Index view of the model management section
        Just render index template
        """
        return self.render( 'index', request, {} )


    def add_view(self, request):
        """
        Add a model instance
        """
        form_class = self.add_form_class or self.form_class
        if request.method == "POST":
            form = form_class(data=request.POST, files=request.FILES)
            if form.is_valid():
                item = form.save()
                self.add_message(request, self.MSG_ADDED)
                return self.redirect('edit', request, item.id)
        else:
            form = form_class()
        context = {
            'form': form,
            }
        return self.render( 'add', request, context )


    def edit_view(self, request, item_id):
        """
        Edit item view
        """
        form_class = self.form_class
        return self._form_view(request, item_id, form_class)


    def delete_view(self, request, item_id):
        """
        Delete item view
        """
        item = self.get_object(item_id)
        if request.method == "POST":
            item.delete()
            self.add_message(request, self.MSG_DELETED)
            redir_to = request.POST.get('redirect')
            if redir_to:
                return self.redirect(redir_to, request)
            context = {
                'item': item,
            }
            return self.render('item_deleted', request, context)

        context = {
            'item': item,
            'redirect': request.META['HTTP_REFERER'] if request.GET.get('back') else "",
            }
        return self.render('delete', request, context)


    def _form_view(self, request, item_id, form_class, action='edit', **context):
        """
        A generic form display-parse-save view
        Arguments:
            action: the name common for the view and template
        After a successful form parse and save, redirect to the same action
        """
        item = self.get_object(item_id)

        if request.method == "POST":
            form = form_class(instance=item, data=request.POST, files=request.FILES)
            if form.is_valid():
                item = form.save()
                self.add_message(request, self.MSG_SAVED)
                #if not request.is_ajax():
                return self.redirect(action, request, item.id)
                # for ajax requests, re-render template with updated values
        else:
            form = form_class(instance=item)
        context.update({
            'form': form,
            'item': item,
        })
        return self.render( action, request, context )


    def render(self, action, request, context={}):
        """
        Render a template
        """
        tpl = self.identify_template(action, is_ajax=request.is_ajax())
        context.update({
            'dispatcher': self, # some yzadmin_tags depend on it
            'action': action,
            'model_name': self.name,
            'model_title': self.title,
            'model_title_plural': self.title_plural,
            #'messages': self.fetch_messages(request),
        })
        if not request.is_ajax():
            context.update({
                'menu': Dispatcher.get_menu(),
            })
        # any additional context vars (e.g. in mixins)
        if hasattr(self, 'update_context'):
            self.update_context(request, context)
        return render_to_response(tpl, RequestContext(request, context))


    def redirect(self, action, request, *args):
        """
        Redirect to an action within the dispatcher,
            or to a location given by full-path (if action contains slashes)
        """
        url = None
        if "/" in action:
            try:
                # remove url-scheme and domain from redirect-url
                tmp = action.split("://", 1)[1]
                url = "/%s" % tmp.split("/", 1)[1]
            except IndexError:
                action = 'index'
        if not url:
            url = reverse('yzadmin_dispatcher_view', kwargs={
                'arg': '%s/%s/%s' % (
                            self.name,
                            action,
                            '/'.join([str(arg) for arg in args])
                )
            })
        if request.is_ajax():
            return http.HttpResponse('<script>document.location.href="%s"</script>' % url)
        return http.HttpResponseRedirect(url)


    def get_object(self, item_id):
        """
        shortcut for getting a model instance
        """
        try:
            return self.model.objects.get(pk=item_id)
        except ObjectDoesNotExist:
            raise ItemNotFoundException(item_id=item_id)


    def add_message(self, request, msg):
        """
        Add a message which will be displayed after redirect
        A message (defined in the class) idenfitied by msg will be added to session
            (via messages framework)
        """
        msg = self.messages.get(msg, msg)
        messages.info(request, msg)


class TabsDispatcher(ModelDispatcher):
    """
    Add Tabs functionality to model dispatcher
    tab descriptor format:
        name, title, form_class
          form_class: None means a ModelForm for the model
        e.g.
        ('data', 'Data', DataForm),
        ('stuff', 'Stuff', None),
        NOTE:
        for each tab, a view def {name}_name() must exist
        which will be used for tab handling
    """
    tabs_descriptor = (
        ('data', _('data'), None),
    )


    def __init__(self, model=None):
        super(TabsDispatcher, self).__init__(model)
        self.init_tabs()


    def _process(self, request, view, *args):
        try:
            return super(TabsDispatcher, self)._process(request, view, *args)
        except ViewNotFoundException:
            logger.debug("View %s not found, trying edit/ID/%s", view, view)
            args += (view, )
            return super(TabsDispatcher, self)._process(request, 'edit', *args)

    def edit_view(self, request, item_id, tab_name=None):
        """
        Edit item view -> override ModelDispatcher's
        If tabs are defined, render (and parse form for) a specific tab
        """

        logger.debug("Edit tab: %s", tab_name)
        tab_name = tab_name or request.session.get('%s_last_tab' % self.name,
                self.tabs[0]['name'])
        try:
            tab_view = getattr(self, '%s_view' % tab_name)
        except AttributeError:
            if tab_name in self.tabs_by_name:
                return self._form_tab_view(request, item_id, tab_name)
            raise ViewNotFoundException(view=tab_name)
        else:
            return tab_view(request, item_id)



    def xxxinit_tabs(self):
        """
        Get the list of tabs used
        (On first run, read and transform the tabs descriptor)
        """
        tabs = []
        tabs_by_name = {}
        for tab_name, tab_title, form_class in self.tabs_descriptor:
            # if a def {tab_name}_view() exists, it will be used for tab handling
            #view_name = "%s_view" % tab_name
            #view = getattr(self,  view_name, None)
            #if view is not None:
                tab = {
                    'name': tab_name,
                    'title': tab_title,
                    'form_class': form_class,
                    'disabled': False,
                }
                tabs.append(tab)
                tabs_by_name[tab_name] = tab
        self.tabs = tabs
        self.tabs_by_name = tabs_by_name
        return self.tabs


    def init_tabs(self):
        """
        Get the list of tabs used
        (On first run, read and transform the tabs descriptor)
        """
        tabs = []
        tabs_by_name = {}
        descriptor = []
        # find all tabs_descriptors in base classes
        for cls in reversed(self.__class__.__mro__):
            try:
                descriptor.extend(cls.tabs_descriptor)
            except AttributeError:
                pass
        for tab_name, tab_title, attrs in descriptor:
            #
            if isinstance(attrs, dict):
                form_class = attrs.pop('form_class', None)
                tab = attrs
                if form_class == "auto":
                    form_class = self._create_tab_form(tab_name,
                                    fields=tab['fields'],
                                    widgets=tab.get('widgets'))
            else:
                form_class = attrs
                tab = {}

            tab.update({
                'name': tab_name,
                'title': tab_title,
                'form_class': form_class,
            })

            # save tab by name
            try:
                tabs_by_name[tab_name].update(tab)
            except KeyError:
                tabs_by_name[tab_name] = tab
                tabs.append(tab)

        tabs.sort(lambda a,b: cmp(a.get('index', 100), b.get('index', 100)))
        self.tabs = tabs
        self.tabs_by_name = tabs_by_name
        return self.tabs


    def render_tab(self, action, request, context):
        """
        Render a tab
        The action is at the same time the rendered tab's name
        """
        request.session['%s_last_tab' % self.name] = action
        context.update({
            'tabs': self.tabs,
            'current_tab': self.tabs_by_name[action],
        })
        return self.render(action, request, context)


    def _form_tab_view(self, request, item_id, tab_name):
        """
        A generic form display-parse-save view, for tabs
        """
        # assert that the name corresponds to a defined tab ...
        request.session['%s_last_tab' % self.name] = tab_name
        tab = self.tabs_by_name[tab_name]
        # ... and the tab has form class defined
        form_class = tab['form_class']
        return self._form_view(request, item_id, form_class, action=tab_name,
            current_tab=tab, tabs=self.tabs)


    def _create_tab_form(self, tab_name, fields, widgets=None):
        """ Create a form class for tab using given fields """
        class _Meta:
            model = self.model
        _Meta.fields = fields
        if widgets:
            _Meta.widgets = widgets

        class _Form(forms.ModelForm):
            Meta = _Meta

        return _Form


class PageDispatcherMixin(object):
    """
    A dispatcher mixin for models for which paging is applicable
    """
    items_per_page = 12


    def get_page(self, request, item=None):
        """
        Get a page of items
        Arguments:
            item: a model instance
                    - used to refine pages to some attributes of the item
                      and mark item current
        """

        items = self._get_page_items(request, item)

        page_nr = request.GET.get("page")
        if not page_nr:
            if item:
                try:
                    items = tuple(items)
                    idx = items.index(item)
                except ValueError:
                    page_nr = None
                    #logger.exception("%s: item: %s", self.__class__.__name__, item)
                else:
                    page_nr = int(idx / self.items_per_page) + 1
                    #logger.debug("%s: idx: %s, page: %s", self.__class__.__name__, idx, page_nr)
            if not page_nr:
                try: # restore last opened page for the dispatcher
                    page_nr = request.session['%s_last_page' % self.name]
                except KeyError:
                    page_nr = 1

        paginator = Paginator(items, self.items_per_page)
        try: # avoid failures when deleting a last item on last page
            page = paginator.page(page_nr)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        request.session['%s_last_page' % self.name] = page.number
        return page


    def page_view(self, request):
        """
        Get an inline (if AJAX) page listing, or an index view with the requested page
        """
        if not request.is_ajax():
            #
            pass
        # try to get item
        item = request.GET.get("item_id")
        if item:
            try:
                item = self.model.objects.get(pk=item)
            except self.model.DoesNotExist:
                item = None
        context = {
            'item': item,
            'page': self.get_page(request, item),
            'page_url': reverse('yzadmin_dispatcher_view', kwargs={
                            'arg': '%s/page' % self.name
                        }),
        }
        return self.render( 'page', request, context )


    def _get_page_items(self, request, item=None):
        return self.model.objects.all()



class MetaDispatcherMixin(object):
    """
    A tabbed dispatcher mixin for MetaInfo models
    """
    tabs_descriptor = (
        ('meta', _('Meta'), {
            'index': 200,
            'form_class': 'auto',
            'fields': ('meta_title', 'meta_keywords', 'meta_description'),
            }),
    )



class ImageDispatcherMixin(object):
    """
    A dispatcher mixin for models which have images (i.e. item.images relation)
    NOTE: requires TabsDispatcher
    """
    add_image_form_class = None

    def _get_image_edit_form_class(self, item):
        class ImageEditForm(forms.ModelForm):
            class Meta:
                model = item.images.model
                fields = ('position', 'title')
        return ImageEditForm

    def images_view(self, request, item_id):
        """
        List of item's images
        """
        item = self.get_object(item_id)
        form = self.add_image_form_class()
        context = {
            'item': item,
            'images': item.images.all(),
            'form': form,
        }
        return self.render_tab( 'images', request, context )


    def add_image_view(self, request, item_id):
        """
        Add image to an instance
        """
        item = self.get_object(item_id)
        if request.method == "POST":
            form = self.add_image_form_class(data=request.POST, files=request.FILES)
            if form.is_valid():
                imagerel = item.images.create(**form.cleaned_data)
                #imagerel.save()
                self.add_message(request, self.MSG_ADDED)
            else:
                self.add_message(request, self.MSG_ERROR)
            return self.redirect('images', request, item.id)
        else:
            form = self.add_image_form_class()

        context = {
            'item': item,
            'form': form,
        }
        return self.render( 'add_image', request, context )

    def delete_image_view(self, request, item_id):
        """
        Delete an image of instance
        """
        item = self.get_object(item_id)
        if request.method == "POST":
            try:
                image_id = request.POST['image']
                img = item.images.get(id=image_id)
                img.delete()
            except:
                self.add_message(request, self.MSG_ERROR)
            else:
                self.add_message(request, self.MSG_DELETED)
            return self.redirect('images', request, item.id)

        context = {
            'item': item,
            'image': request.GET.get('image'),
        }
        return self.render( 'delete_image', request, context )


    def edit_image_view(self, request, item_id):
        """
        Edit image's attributes
        """
        item = self.get_object(item_id)
        image_id = request.GET.get('image')
        ImageEditForm = self._get_image_edit_form_class(item)
        try:
            img = item.images.get(id=image_id)
        except ObjectDoesNotExist:
            raise ItemNotFoundException(item_id=image_id)

        if request.method == "POST":
            form = ImageEditForm(data=request.POST, instance=img)
            if form.is_valid():
                form.save()
                return self.redirect('images', request, item.id)
        else:
            form = ImageEditForm(instance=img)

        context = {
            'item': item,
            'image': img,
            'form': form,
        }
        return self.render( 'edit_image', request, context )


class PageDispatcher(ModelDispatcher, PageDispatcherMixin):
    pass

