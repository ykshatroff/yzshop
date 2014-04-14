
from django import forms
#from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _


from .models import Question

from yz.admin.dispatchers import Dispatcher
from yz.admin.dispatchers import PageDispatcherMixin
from yz.admin.dispatchers import TabsDispatcher
from yz.admin.dispatchers import ItemNotFoundException

from yz.admin.forms import CalendarWidget
from yz.admin.forms import TinyMCEWidget

# ### Question forms
class QuestionAddForm(ModelForm):
    class Meta:
        model = Question
        fields = ('name', 'slug')


class QuestionDataForm(ModelForm):
    class Meta:
        model = Question
        exclude = ('meta_title', 'meta_keywords', 'meta_description')
        widgets = {
            'answer': TinyMCEWidget,
            'date_created': CalendarWidget,
        }

class QuestionMetaForm(ModelForm):
    class Meta:
        model = Question
        fields = ('meta_title', 'meta_keywords', 'meta_description')



# ### Dispatchers
# ### QuestionDispatcher
class QuestionDispatcher(TabsDispatcher, PageDispatcherMixin):
    """
    The Question model dispatcher for YZ management `console`
    """
    add_form_class = QuestionAddForm

    tabs_descriptor = (
        ('data', _(u'data'), QuestionDataForm),
        # probably add some stats or smth
        ('meta', _(u'Meta'), QuestionMetaForm),
    )

    def data_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'data')

    def meta_view(self, request, item_id):
        return self._form_tab_view(request, item_id, 'meta')



Dispatcher.register(QuestionDispatcher(Question), menuitem='content')
