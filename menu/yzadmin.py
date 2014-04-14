from __future__ import unicode_literals

from django import forms
#from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import MenuGroup
from .models import MenuItem

from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import ItemNotFoundException, BadParameterException
from yz.admin.urls import admin_reverse


class ParentItemWidget(forms.HiddenInput):
    is_hidden = False
    menu_item_id = None

    def render(self, name, value, attrs=None):
        text = None
        kwargs = {
            'item_id': self.menu_item_id,  # the id of the menu item instance (field owner)
            'current_value': value,  # the current parent id
        }
        if value:
            try:
                menuitem = MenuItem.objects.get_cached(id=value)
            except MenuItem.DoesNotExist:
                value = None
            else:
                text = unicode(menuitem)
        else:
            text = _('(Top-level item)')

        html = super(ParentItemWidget, self).render(name, value, attrs)
        html += format_html('<a class="ajax-select with-dialog" href="{0}" title="{2}">{1}</a>',
                            admin_reverse('menuitem', 'select_menuitem', **kwargs),
                            text,
                            _('Select parent menu item'))
        return html


# ### MenuItem forms
class MenuItemAddForm(ModelForm):
    class Meta:
        model = MenuItem
        fields = ('title', 'link', 'group', 'parent')
        widgets = {
            'group': forms.HiddenInput,
            'parent': forms.HiddenInput,
        }


class MenuItemForm(ModelForm):
    class Meta:
        model = MenuItem
        exclude = ('group', 'content_type', 'object_id')


def get_MenuItemForm(*args, **kwargs):
    instance = kwargs.get('instance')
    if instance:
        class parent_widget_class(ParentItemWidget):
            menu_item_id = instance.id
    else:
        parent_widget_class = ParentItemWidget

    class _MenuItemForm(ModelForm):
        class Meta:
            model = MenuItem
            exclude = ('group', 'content_type', 'object_id')
            widgets = {
                'parent': parent_widget_class,
            }
    return _MenuItemForm(*args, **kwargs)


class MenuGroupForm(ModelForm):
    class Meta:
        model = MenuGroup


# ### Dispatchers
# ### MenuItemDispatcher
class MenuItemDispatcher(TabsDispatcher):
    """
    The MenuItem model dispatcher for YZ management `console`
    """
    add_form_class = MenuItemAddForm
    form_class = MenuItemForm

    tabs_descriptor = (
        ('data', _('Data'), get_MenuItemForm),
    )

    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')

    def add_menuitem_view(self, request, item_id):
        """
        Add menuitem to a group
        """
        item = self.get_object(item_id)

        form = MenuItemAddForm(initial=dict(parent=item, group=item.group))

        context = {
            'item': item,
            'form': form,
        }
        return self.render('add_menuitem', request, context)

    def select_menuitem_view(self, request, item_id):
        """
        An AJAX view to select parent menuitem
        @param request: the HTTP request
        @param item_id: the id of the menuitem
        @return: HTTPResponse
        """
        try:
            menuitem = MenuItem.objects.get(id=item_id)
        except MenuItem.DoesNotExist:
            raise ItemNotFoundException(item_id)
        menugroup = menuitem.group

        # all_items = menugroup.get_items_tree()
        context = {
            'menugroup': menugroup,
            'menuitem': menuitem,
        }
        return self.render('select_menuitem', request, context)


    def get_left_menu(self, context):
        """ List of all menu groups """
        return MenuGroup.objects.all()


# ### MenuGroupDispatcher
class MenuGroupDispatcher(TabsDispatcher):
    """
    """
    #form_class = MenuGroupForm

    tabs_descriptor = (
        ('data', _('Data'), MenuGroupForm),
        ('menuitems', _('Menu Items'), None),
    )

    def index_view(self, request):
        """ Go directly to the first menu group's items if available """
        try:
            first_menu = MenuGroup.objects.all()[0]
        except:
            return super(MenuGroupDispatcher, self).index_view(request)
        else:
            return self.redirect('menuitems', request, first_menu.id)


    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')

    def menuitems_view(self, request, item_id):
        """
        List of menuitems assigned to a group
        """
        item = self.get_object(item_id)

        context = {
            'item': item,
            'menuitems': item.items.all(),
            'form': MenuItemAddForm(initial=dict(parent=None, group=item)),
        }
        return self.render_tab( 'menuitems', request, context )

    def add_menuitem_view(self, request, item_id):
        """
        Add menuitem to a group
        """
        item = self.get_object(item_id)

        form = MenuItemAddForm(initial=dict(parent=None, group=item))

        context = {
            'item': item,
            'form': form,
        }
        return self.render('add_menuitem', request, context)

    def get_left_menu(self, context):
        """ List of all menu groups """
        return self.model.objects.all()


def setup(dispatcher):
    # add MenuGroup entry to the 'content' section of admin-menu
    dispatcher.register(MenuGroupDispatcher(MenuGroup), menuitem='content')
    # do not add any
    dispatcher.register(MenuItemDispatcher(MenuItem))
