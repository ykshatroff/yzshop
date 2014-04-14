import logging

from django import http
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Cart
from yz.catalog.models import Product

def cart_view(request, template_name="cart/list.html"):
    """
    TODO:
    """
    cart = Cart.get_cart(request)
    #if not cart:
        #return empty_cart(request)

    response = render_to_response(template_name, RequestContext(request, {
        'cart': cart,
    }))
    return response

@require_POST
def refresh_cart_view(request):
    """
    TODO:
    """
    cart = Cart.get_cart(request)
    if cart:
        cart.refresh(request.POST)
        messages.success(request, _('Cart refreshed.'))
    return http.HttpResponseRedirect(reverse('yz_cart'))

@require_POST
def add_to_cart_view(request):
    """
    Add a variant to cart
    Requires POST[product_id] as the variant's id
    """
    # verify arguments
    item_id = request.POST.get("product_id")
    if not item_id:
        return invalid_argument(request)

    # verify arguments
    try:
        item = Product.objects.get_cached(id=item_id)
    except Product.DoesNotExist:
        return invalid_argument(request)

    cart = Cart.get_or_create_cart(request)
    quantity = request.POST.get("quantity", 1)
    try:
        cart.add_item(item, quantity)
    except ValueError:
        return invalid_argument(request)

    if request.is_ajax():
        # TODO
        # return a message ### HTML code for updated cart-info (template)
        return http.HttpResponse('{"added": %d}' % item.id)

    messages.success(request, _('Product added to cart.'))

    # redirect to the product which has just been added
    return http.HttpResponseRedirect(reverse('yz_catalog_product',
            kwargs={'slug': item.slug}))


#@require_POST
def remove_from_cart_view(request, id):
    """
    Remove a variant from cart
        ### ??? Requires POST[product_id] as the variant's id ???
    Do not need POST because this is one-time action (i.e. repeating it changes nothing)
    """
    cart = Cart.get_cart(request)
    try:
        cart.remove_item(id)
    except ObjectDoesNotExist:
        raise http.Http404
    if request.is_ajax():
        # TODO
        # return a message ### depends on where it was called from
        # return a message ### HTML code for updated cart-info (template)
        # in any case, must update cart totals
        return http.HttpResponse('{"removed": %d}' % id)
    messages.success(request, _('Product removed from cart.'))
    return http.HttpResponseRedirect(reverse('yz_cart'))

def invalid_argument(request):
    """
    """
    if request.is_ajax():
        pass
    return http.HttpResponseBadRequest("Invalid argument")
