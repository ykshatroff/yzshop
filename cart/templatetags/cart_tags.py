from django import template
register = template.Library()

from ..models import Cart

@register.inclusion_tag('cart/tags/cart-info.html', takes_context=True)
def cart_info(context):
    """
    Display the cart info
    """
    cart = Cart.get_cart(context['request'])
    return {
        'CART': cart,
        'cart': cart,
    }
