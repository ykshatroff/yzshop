from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .models import Question

class QuestionForm(forms.ModelForm):
    author = forms.CharField(label=_(u'your name'), max_length=120, required=True)
    company_name = forms.CharField(label=_(u'your company'), max_length=100, required=False)
    job = forms.CharField(label=_(u'your position'), max_length=100, required=False)
    author_email = forms.EmailField(label=_(u'your e-mail'), max_length=50, required=True)

    class Meta:
        model = Question
        fields = ('author', 'job', 'company_name', 'author_email', 'question')

    def clean(self):
        data = self.cleaned_data
        if self._errors:
            return data
        try:
            author_data = [ data['author'], ]
        except KeyError:
            #self._errors['author'] =
            raise forms.ValidationError("No author")
        if data['job']:
            author_data.append(data['job'])
        if data['company_name']:
            author_data.append(data['company_name'])
        data['author'] = ", ".join(author_data)
        return data
