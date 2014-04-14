from django import forms
from .models import UploadedImage

class TinyMCEWidget(forms.Textarea):
    """ Wrapper for Textarea, only to add the TinyMCE-enabling CSS class """
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        css = attrs.get('class', "")
        attrs['class'] = "%s yzadmin-tinymce" % css
        super(TinyMCEWidget, self).__init__(attrs)

class CalendarWidget(forms.DateInput):
    """ Wrapper for DateInput, only to add the calendar-enabling CSS class """
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        css = attrs.get('class')
        attrs['class'] = "%s yzadmin-calendar" % css
        super(CalendarWidget, self).__init__(attrs)

class ParentChoiceWidget(forms.Select):
    """ Parent choice """
    def render(self, name, value, attrs=None, choices=()):
        pass

class TinyMCEImageUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedImage
        fields = ('name', 'image')

