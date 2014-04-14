from django import forms
from django.utils.translation import ugettext_lazy as _

from yz.customer.forms import CustomerForm
from yz.customer.forms import AddressForm
from yz.customer.models import Customer

from .models import DeliveryMethod
from .models import PaymentMethod


def get_order_form_class():
    """
    Get a configured order_form_class or OrderForm
    TODO: import the configured symbol
    """
    return OrderForm

def get_address_form_class():
    """
    Get a configured address_form_class or AddressForm
    TODO: import the configured symbol
    """
    return AddressForm


def _get_initial_delivery_method():
    try:
        x = DeliveryMethod.objects.active()[0]
    except IndexError:
        x = None
    return x

def _get_initial_payment_method():
    try:
        x = PaymentMethod.objects.active()[0]
    except IndexError:
        x = None
    return x

class OrderForm(forms.Form):
    """
    Choose services
    TODO:
        - mutual dependencies btw delivery and payment methods
    """
    delivery_method = forms.ModelChoiceField(queryset=DeliveryMethod.objects.active(),
            widget=forms.RadioSelect,
            initial=_get_initial_delivery_method,
            label=_(u'delivery method'))

    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.active(),
            widget=forms.RadioSelect,
            initial=_get_initial_payment_method,
            label=_(u'payment method'))
    # discount_card
    # voucher

