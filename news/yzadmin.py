
from django import forms
#from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _


from .models import News

from yz.admin.dispatchers import Dispatcher
from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import ItemNotFoundException

from yz.admin.forms import CalendarWidget
from yz.admin.forms import TinyMCEWidget

# ### News forms
class NewsAddForm(ModelForm):
    class Meta:
        model = News
        fields = ('name', 'slug')


class NewsDataForm(ModelForm):
    class Meta:
        model = News
        exclude = ('meta_title', 'meta_keywords', 'meta_description')
        widgets = {
            'body': TinyMCEWidget,
            'date_created': CalendarWidget,
        }

class NewsMetaForm(ModelForm):
    class Meta:
        model = News
        fields = ('meta_title', 'meta_keywords', 'meta_description')



# ### Dispatchers
# ### NewsDispatcher
class NewsDispatcher(TabsDispatcher, PageDispatcherMixin):
    """
    The News model dispatcher for YZ management `console`
    """
    add_form_class = NewsAddForm

    tabs_descriptor = (
        ('data', _(u'data'), NewsDataForm),
        # probably add some stats or smth
        #('products', 'Products', None),
        #('variants', 'Variants', ProductVariantsForm),
        ('meta', _(u'meta'), NewsMetaForm),
    )

    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')

    def meta_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'meta')



Dispatcher.register(NewsDispatcher(News), menuitem='content')
