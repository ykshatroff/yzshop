
from django import forms
#from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import Page

from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import ItemNotFoundException

#from yz.admin.forms import CalendarWidget
from yz.admin.forms import TinyMCEWidget

try:
    from yz.menu.dispatchers import MenuItemDispatcherMixin
except ImportError:
    class MenuItemDispatcherMixin(object):
        pass

# ### Page forms
class PageAddForm(ModelForm):
    class Meta:
        model = Page
        fields = ('name', 'slug')


class PageDataForm(ModelForm):
    class Meta:
        model = Page
        exclude = ('meta_title', 'meta_keywords', 'meta_description')
        widgets = {
            'body': TinyMCEWidget,
            #'date_created': CalendarWidget,
        }

class PageMetaForm(ModelForm):
    class Meta:
        model = Page
        fields = ('meta_title', 'meta_keywords', 'meta_description')



# ### Dispatchers
# ### PageDispatcher
class PageDispatcher(TabsDispatcher, PageDispatcherMixin, MenuItemDispatcherMixin):
    """
    The Page model dispatcher for YZ management `console`
    """
    add_form_class = PageAddForm

    tabs_descriptor = (
        ('data', _('Data'), PageDataForm),
        ('menu', _('menu'), None),
        # probably add some stats or smth
        ('meta', _('Meta'), PageMetaForm),
    )

    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')


    def meta_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'meta')


def setup(dispatcher):
    dispatcher.register(PageDispatcher(Page), menuitem='content')
