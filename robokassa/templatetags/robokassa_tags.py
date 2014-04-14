from django import template
from yz.robokassa.utils import get_payment_url

register = template.Library()

@register.simple_tag
def robokassa_url(order):
    """
    """
    if not order:
        return ''

    url = get_payment_url(order)
    return url
