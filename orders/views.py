# django imports
from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
#from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext

# module imports
from yz.cart.models import Cart
from yz.customer.models import Customer
from yz.customer.models import CustomerAddress
from yz.customer.forms import CustomerForm
from .forms import get_address_form_class
from .forms import get_order_form_class
from .models import Order
from .models import OrderAddress
from .models import DeliveryMethod
from .models import PaymentMethod

def order_form_view(request, template_name="orders/form.html"):
    """
    Display a number of forms if GET,
    parse the forms and redirect to order if POST
    """
    cart = Cart.get_cart(request)
    if not cart:
        return http.HttpResponseRedirect(reverse("yz_cart"))

    customer = Customer.get_or_create_customer(request)
    _OrderForm = get_order_form_class() # selected services and discount documents
    _AddressForm = get_address_form_class() # customer address if required by services

    is_valid = None
    if request.method == "POST":
        customer_form = CustomerForm(data=request.POST, instance=customer)
        if customer_form.is_valid() and customer.is_blank():
            # if customer data is not filled in,
            # save customer using the input data
            customer = customer_form.save()
        if not customer.primary_address:
            # create customer's address if none exists
            # this will also save customer and assign primary_address
            addr = customer.addresses.create( customer=customer, )
        order_form = _OrderForm(data=request.POST)

        # ### set up default address fields' data in case address not required
        address_required = False
        if order_form.is_valid():
            address_required = getattr(order_form.cleaned_data.get("delivery_method"),
                                        "address_required", False)
            if not address_required:
                address_required = getattr(order_form.cleaned_data.get("payment_method"),
                                        "address_required", address_required)

        # instantiate address_form regardless whether address_required
        # because we can't know that exactly before order_form validation
        # but we must keep any data the user filled in
        address = OrderAddress.from_address(customer.primary_address)
        address_form = _AddressForm(address_required=address_required,
                data=request.POST, instance=address)
        # NOTE: may use data.setdefault() for fields shared between
        # _AddressForm and CustomerForm

        if (customer_form.is_valid()
                and order_form.is_valid()
                and address_form.is_valid()):
            address_form.save()
            order = Order.create_order(cart=cart, customer=customer,
                    address=address,
                    order_data=order_form.cleaned_data)
            # save order to session for the 'completed' view only
            request.session['order'] = order.id
            cart.clear(request)
            return http.HttpResponseRedirect(reverse("yz_order_completed"))
    else:
        customer_form = CustomerForm(instance=customer)
        order_form = _OrderForm()
        # use customer's saved address as initial data for OrderAddress
        address_form = _AddressForm(instance=customer.primary_address)


    response = render_to_response(template_name, RequestContext(request, {
        'cart': cart,
        'customer': customer,
        'order_form': order_form,
        'customer_form': customer_form,
        'address_form': address_form,
        'is_valid': is_valid,
    }))
    return response


def order_completed_view(request, template_name="orders/thank-you.html"):
    'One gets redirected here after completing order form'
    customer = Customer.get_customer(request)
    try:
        # remove order from session
        order_id = request.session.pop('order')
        order = Order.objects.get(id=order_id)
    except (KeyError, Order.DoesNotExist):
        return http.HttpResponseRedirect(reverse("yz_cart"))

    response = render_to_response(template_name, RequestContext(request, {
        'order': order,
    }))
    return response
