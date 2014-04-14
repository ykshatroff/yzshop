from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from . import settings

class PriceField(models.DecimalField):
    """
    The price field for models which use prices
    """
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            #default=0,
            max_digits=settings.PRICE_DECIMAL_DIGITS,
            decimal_places=settings.PRICE_DECIMAL_PLACES
        ))
        super(PriceField, self).__init__(*args, **kwargs)


class OverrideFormField(forms.BooleanField):
    """ A special form field for overriding product's properties """
    pass

class OverrideField(models.BooleanField):
    """ A special model field for overriding product's properties """

    def __init__(self, *args, **kwargs):
        """
        Setup
        Kwargs:
            copy_parent: whether to copy variant's value
                         for the original field from parent's
        """
        self.copy_parent = kwargs.pop('copy_parent', True)
        defaults = {
            'default': False,
            'verbose_name': args[0] if args else _(u"override"),
        }
        defaults.update(kwargs)
        super(OverrideField, self).__init__(**defaults)

    def formfield(self, **kwargs):
        defaults = {'form_class': OverrideFormField}
        defaults.update(kwargs)
        return super(OverrideField, self).formfield(**defaults)
