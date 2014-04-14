from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from yz.core.models import Shop
from yz.core.models import StaticBlock

from yz.admin.dispatchers import PageDispatcher
from yz.admin.dispatchers import TabsDispatcher

from yz.admin.forms import TinyMCEWidget

class ShopDataForm(ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'domain', 'from_email', 'notification_emails', 'address', 'phones', 'static_block')
        #exclude = ('meta_title', 'meta_keywords', 'meta_description',
                #'google_analytics_id', 'ga_site_tracking', 'ga_ecommerce_tracking')

class ShopDescriptionForm(ModelForm):
    class Meta:
        model = Shop
        fields = ('description', )
        widgets = {
            'description': TinyMCEWidget,
        }

class ShopMetaForm(ModelForm):
    class Meta:
        model = Shop
        fields = ('meta_title', 'meta_keywords', 'meta_description')

class StaticBlockAddForm(ModelForm):
    class Meta:
        model = StaticBlock
        fields = ('name', )

class StaticBlockForm(ModelForm):
    class Meta:
        model = StaticBlock
        widgets = {
            'html': TinyMCEWidget,
        }

# ### Dispatchers

class ShopDispatcher(TabsDispatcher):
    """
    """

    tabs_descriptor = (
        ('data', _('Data'), ShopDataForm),
        ('description', _('description'), ShopDescriptionForm),
        ('meta', _('Meta'), ShopMetaForm),
    )

    def index_view(self, request):
        return self.redirect('edit', request, 1)

    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')

    def description_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'description')

    def meta_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'meta')


class StaticBlockDispatcher(PageDispatcher):
    """
    """
    add_form_class = StaticBlockAddForm
    form_class = StaticBlockForm


def setup(dispatcher):
    dispatcher.register(ShopDispatcher(Shop), menuitem='shop', title=_(u'shop'))
    dispatcher.register(StaticBlockDispatcher(StaticBlock), menuitem='content')

