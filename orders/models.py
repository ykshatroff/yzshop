import decimal
import uuid
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime


from yz.catalog.models import PriceField
from yz.catalog.models import Product
from yz.catalog.models import Property
from yz.customer.models import Customer
from yz.customer.models import Address

from .managers import ServiceManager
from .signals import order_created
from .signals import order_status_changed

get_uuid = lambda: str(uuid.uuid4())


class Service(models.Model):
    """
    """
    name = models.CharField(_(u"name"), max_length=50)
    slug = models.SlugField(_(u"slug"), unique=True,
            help_text=_(u'this field is required for handlers to work'))
    price = PriceField(_(u"cost"))
    position = models.IntegerField(_(u'position'), default=100)
    active = models.BooleanField(_(u'active'))
    description = models.TextField(_(u"description"), blank=True)
    address_required = models.BooleanField(_(u"address required"),
            help_text=_(u"customer's address is required to use the service"))

    class Meta:
        abstract = True
        ordering = ('position', )

    def __unicode__(self):
        return self.name


class DeliveryMethod(Service):
    """
    """

    objects = ServiceManager()

    class Meta:
        verbose_name = _(u'delivery method')
        verbose_name_plural = _(u'delivery methods')



class PaymentMethod(Service):
    """
    """
    is_prepayment = models.BooleanField(_(u"prepayment"),
            help_text=_(u"whether this type of payment is prepayment"))

    objects = ServiceManager()

    class Meta:
        verbose_name = _(u'payment method')
        verbose_name_plural = _(u'payment methods')


class OrderAddress(Address):
    """
    Concrete class for abstract Address model
    Stores addresses for orders, when required
    Allows to easily copy data from CustomerAddress
    """

    @classmethod
    def from_address(cls, address):
        """
        Instantiate new address with a copy of an Address instance data
        Arguments:
            address: an instance of Address
        """
        return cls().copy_address(address)

    def copy_address(self, address):
        """
        Make a copy of address as an OrderAddress instance
        Copy all explicitly defined fields except id
        Arguments:
            address: an instance of Address
        """
        for field in self._meta.local_fields:
            setattr(self, field.name, getattr(address, field.name))
        self.id = None
        return self


class Order(models.Model):
    """
    Order Entry.
    TODO:
    - cancelled is mut.ex. with closed
    - whether verified is required to pay

    """

    NUMBER_FORMAT = "%d"

    STATUS_NEW = 0
    STATUS_PAID = 10
    STATUS_SENT = 20
    STATUS_CANCELLED = -1
    STATUS_CLOSED = 128
    STATUS_LABELS = {
        STATUS_NEW: 'new',
        STATUS_PAID: 'paid',
        STATUS_SENT: 'sent',
        STATUS_CANCELLED: 'cancelled',
        STATUS_CLOSED: 'closed',
    }
    STATUS_CHOICES = (
        (STATUS_NEW, _(u"new")),
        (STATUS_PAID, _(u"paid")),
        (STATUS_SENT, _(u"sent")),
        (STATUS_CLOSED, _(u"closed")),
        (STATUS_CANCELLED, _(u"cancelled")),
    )

    number = models.CharField(_(u"number"), max_length=30, unique=True, blank=True, null=True)
    uid = models.CharField(_(u"UUID"), help_text=_(u"Universally unique order ID"),
            default=get_uuid,
            max_length=50)
    date_submitted = models.DateTimeField(verbose_name=_(u'date submitted'), auto_now_add=True)
    #date_verified = models.DateTimeField(verbose_name=_(u'date verified'), blank=True, null=True)
    date_paid = models.DateTimeField(verbose_name=_(u'date paid'), blank=True, null=True)
    date_sent = models.DateTimeField(verbose_name=_(u'date sent'), blank=True, null=True)
    date_cancelled = models.DateTimeField(verbose_name=_(u'date cancelled'), blank=True, null=True)
    date_closed = models.DateTimeField(verbose_name=_(u'date closed'), blank=True, null=True)
    status = models.PositiveSmallIntegerField(_(u"status"), choices=STATUS_CHOICES,
            default=STATUS_NEW, db_index=True,
            )

    value = PriceField(_(u"order value"), help_text=_(u'the total sum of prices of products'))
    total = PriceField(_(u"order amount to pay"),
            help_text=_(u'the amount to pay, incl. discounts and service costs'))

    delivery_method = models.ForeignKey(DeliveryMethod, verbose_name=_(u'delivery method'),
            blank=True, null=True,
            related_name="+")
    delivery_method_name = models.CharField(_(u"delivery method name"), max_length=100)
    delivery_cost = PriceField(_(u"delivery cost"))

    payment_method = models.ForeignKey(PaymentMethod, verbose_name=_(u'payment method'),
            blank=True, null=True,
            related_name="+")
    payment_method_name = models.CharField(_(u"payment method name"), max_length=100)
    payment_cost = PriceField(_(u"payment cost"))

    # customer info
    # allow blank because customer may occasionally be deleted
    customer = models.ForeignKey(Customer, verbose_name=_(u"customer"), blank=True, null=True,
            on_delete=models.SET_NULL,
            related_name="orders")
    customer_name = models.CharField(_(u"customer's name"), blank=True, max_length=200)
    customer_company_name = models.CharField(_(u"customer's company name"), blank=True, max_length=200)
    customer_email = models.CharField(_(u"customer's email"), max_length=50)
    customer_phone = models.CharField(_(u"customer's phone"), max_length=20)

    # address can be empty in some cases (as when no delivery)
    address = models.ForeignKey(OrderAddress, verbose_name=_(u'customer address'),
            related_name="+", blank=True, null=True)

    message = models.TextField(_(u"customer's message"), blank=True)

    def __unicode__(self):
        return u"%s (%s, %s)" % (self.number, self.date_submitted, self.get_text_status())

    class Meta:
        ordering = ('-date_submitted', )
        get_latest_by = 'date_submitted'
        verbose_name = _(u'order')
        verbose_name_plural = _(u'orders')

    @classmethod
    def calculate(cls, cart, customer, address=None, order_data=None):
        """
        Calculate order total amount from cart and customer instances and specific data
        Return a dict of values directly suitable (as kwargs) to create order from
        The dict of order_data may contain:
        - delivery_method instance
        - payment_method instance
        - voucher instance
        - discount_card instance
        - message text
        The calculate() method can also be used to preview the order total value with selected
            services and discounts
        TODO voucher, discounts, criteria
        """
        if not cart:
            raise ValueError("Can not create order from an empty cart")

        if order_data is None:
            order_data = {}

        delivery_method = order_data.get('delivery_method')
        delivery_cost = delivery_method.price if delivery_method else 0
        payment_method = order_data.get('payment_method')
        payment_cost = payment_method.price if payment_method else 0

        # TODO it must be defined how voucher discounts are calculated
        # TODO e.g. percentage or real value, and if the former, then to which amount it applies
        #voucher = order_data.get('voucher')
        #voucher_discount = voucher.get_discount_value(cart.value)

        total = cart.value + delivery_cost + payment_cost

        return dict(customer=customer,
                customer_name=customer.name,
                customer_company_name=customer.company_name,
                customer_email=customer.email,
                customer_phone=customer.phone,
                address=address,
                delivery_method=delivery_method,
                delivery_method_name="%s" % delivery_method,
                delivery_cost=delivery_cost,
                payment_method=payment_method,
                payment_method_name="%s" % payment_method,
                payment_cost=payment_cost,
                value=cart.value,
                total=total,
                message=order_data.get('message', ""),
            )

    @classmethod
    def create_order(cls, cart, customer, address=None, order_data={}):
        """
        Create an order from cart and customer instances and specific data
        - calculate order's amount to pay
        - save all ordered items
        - generate order's number
        """
        kwargs = cls.calculate(cart, customer, address, order_data)

        order = cls(**kwargs)
        order.save()

        # generate number
        order.number = order.get_number()
        order.save()

        # save all ordered items
        for item in cart.get_items():
            OrderItem.from_cart_item(order, item)

        order_created.send(order)

        return order

    def get_number(self):
        return self.NUMBER_FORMAT % self.id

    def is_payable(self):
        """ Whether the order can be paid """
        return not (self.date_paid
                    or self.date_cancelled or self.date_closed)

    def set_status(self, new_status, save=True):
        """
        Set the new status with validity check
        new_status can be given as integer code or string label (see STATUS_LABELS)
        (each valid string label has the corresponding set_%s method)
        STATUS_NEW can not be set
        """
        try:
            label = self.STATUS_LABELS[int(new_status)]
        except:
            label = new_status

        try:
            _set_status = getattr(self, "set_%s" % label)
        except AttributeError:
            raise ValueError("Unknown status code '%s'" % new_status)
        else:
            return _set_status(save=save)


    def set_paid(self, save=True):
        """
        NOTE: can not pay unpayable order (incl. already paid)
        """
        if not self.is_payable():
            raise ValueError("Order can not be paid now")
        previous_status = self.status
        self.date_paid = datetime.now()
        self.status = self.STATUS_PAID
        order_status_changed.send(self, previous_status=previous_status)
        if save:
            self.save()

    def set_closed(self, save=True):
        """
        NOTE: can not close unpaid order
        """
        if not self.date_paid:
            raise ValueError("Order can not be closed now: it must be paid")
        previous_status = self.status
        self.date_closed = datetime.now()
        self.status = self.STATUS_CLOSED
        order_status_changed.send(self, previous_status=previous_status)
        if save:
            self.save()

    def set_sent(self, save=True):
        previous_status = self.status
        self.date_sent = datetime.now()
        self.status = self.STATUS_SENT
        order_status_changed.send(self, previous_status=previous_status)
        if save:
            self.save()

    def set_cancelled(self, save=True):
        previous_status = self.status
        self.date_cancelled = datetime.now()
        self.status = self.STATUS_CANCELLED
        order_status_changed.send(self, previous_status=previous_status)
        if save:
            self.save()

    def undo_status(self, save=True):
        """
        Undo the last status
        """
        if save:
            self.save()


    def get_text_status(self):
        """ Get order status as text """
        for s in self.STATUS_CHOICES:
            if s[0] == self.status:
                return s[1]
        return self.STATUS_NEW

    def get_available_status(self):
        """ Get list of statuses available to set, as list of tuples (nr,text) """
        if self.status in (self.STATUS_CANCELLED, self.STATUS_CLOSED):
            # with these statuses orders can not change their status
            return []
        if self.status == self.STATUS_NEW:
            # all except self.STATUS_NEW, self.STATUS_CLOSED
            return [v for v in self.STATUS_CHOICES
                if v[0] not in (self.STATUS_NEW, self.STATUS_CLOSED)]

        s = [self.STATUS_CANCELLED]
        if self.status == self.STATUS_PAID:
            # can set cancelled, sent (if not yet set) and closed (if sent)
            if self.date_sent:
                s.append(self.STATUS_CLOSED)
            else:
                s.append(self.STATUS_SENT)
        elif self.status == self.STATUS_SENT:
            # can set cancelled, paid (if not yet set) and closed (if paid)
            if self.date_paid:
                s.append(self.STATUS_CLOSED)
            else:
                s.append(self.STATUS_SENT)
        else:
            # else, which shouldn't happen, only CANCEL is available
            pass
        return [v for v in self.STATUS_CHOICES if v[0] in s]

class OrderItem(models.Model):
    """An order items holds the sold product, its amount and some other relevant
    product values like the price at the time the product has been sold.
    """
    order = models.ForeignKey(Order, related_name="items")
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.SET_NULL)

    # name may also contain services such as delivery, payment etc
    name = models.CharField(_(u"product name"), max_length=100)
    sku = models.CharField(_(u"SKU"), blank=True, max_length=50)
    quantity = models.DecimalField(_(u"quantity"), default=0, max_digits=10, decimal_places=3)
    price = PriceField(_(u"product price"))

    class Meta:
        unique_together = ('order', 'product')
        verbose_name = _(u'order item')
        verbose_name_plural = _(u'order items')

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.sku)

    def get_value(self):
        """
        Get the total value of products for this item
        """
        return (self.price * self.quantity).quantize(decimal.Decimal('1.00'))


    @classmethod
    def from_cart_item(cls, order, cart_item):
        """
        Create an entry for an ordered product variant and
            store its properties and values
        """
        variant = cart_item.product
        item = cls.objects.create(
            order=order,
            product=variant,
            name=variant.name,
            sku=variant.sku,
            quantity=cart_item.quantity,
            price=cart_item.price,
        )
        for propval in variant.get_property_values():
            OrderItemPropertyValue.objects.create(
                    order_item=item,
                    property=propval.property,
                    value="%s" % propval.get_value(), # cast to string
            )
        return item


class OrderItemPropertyValue(models.Model):
    """Stores a value for a property and order item.

    **Attributes**

    order_item
        The order item - and in this way the product - for which the value
        should be stored.

    property
        The property for which the value should be stored.

    value
        The value which is stored.
    """
    order_item = models.ForeignKey(OrderItem, verbose_name=_(u"order item"), related_name="properties")
    property = models.ForeignKey(Property, verbose_name=_(u"property"))
    value = models.CharField("value", blank=True, max_length=100)
