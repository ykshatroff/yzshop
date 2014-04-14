from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from yz.cache.managers import CachingManager

from yz.core.models import Country, Shop


class Address(models.Model):
    """
    An abstract address class
    """
    name = models.CharField(_(u"name"), max_length=200)
    company_name = models.CharField(_(u"company name"), max_length=100, blank=True)
    email = models.EmailField(_(u"e-mail"), db_index=True, max_length=50)
    phone = models.CharField(_(u'phone'), max_length=20)
    address = models.TextField(_(u'address'), blank=True)
    # TODO widget for city selection
    town = models.CharField(_(u"town"), blank=True, max_length=100)
    province = models.CharField(_(u"province"), blank=True, max_length=100)
    country = models.ForeignKey(Country, verbose_name=_(u"country"),
                                default=lambda: Shop.get_default_shop().get_default_country())
    zip_code = models.CharField(_(u"zip code"), max_length=10, blank=True)

    class Meta:
        abstract = True
        verbose_name = _(u'address')
        verbose_name_plural = _(u'addresses')

    def __unicode__(self):
        return "%s %s:%s" % (self.first_name, self.last_name, self.phone)


class CustomerAddress(Address):
    """
    NOTE:
    A customer can have many addresses active at once
    Address is localizable: it's possible by subclassing it and specifying local fields
    """
    customer = models.ForeignKey("Customer", verbose_name=_(u"customer"),
            on_delete=models.SET_NULL,
            blank=True, null=True,
            related_name="addresses")

    class Meta:
        verbose_name = _(u'address')
        verbose_name_plural = _(u'addresses')

    def save(self, *args, **kwargs):
        """
        Take some default values from customer and optionally
        assign the address instance as customer's primary address
        """
        customer = self.customer
        if customer:
            #if not self.country:
                #self.country = get_default_country()
            # copy attributes
            for attr in ('name', 'company_name', 'email', 'phone'):
                if not getattr(self, attr):
                    setattr(self, attr, getattr(customer, attr))
        super(CustomerAddress, self).save(*args, **kwargs)
        if customer.id: # ensure that the customer instance is in DB,
            # to avoid unwittingly saving a new customer
            if not customer.primary_address:
                # update customer's primary address - AFTER saving self
                customer.primary_address = self
                customer.save()


class Customer(models.Model):
    """
    Base customer class: represents an identity
    A customer object is created (if not exists) whenever the client:
        - registers and enters any of the fields
        - places order
    NOTE: we do not make fields name,email,phone required because otherwise
        it is not possible to create a customer object without user input
    """
    SESSION_CUSTOMER_ID = "customer_id"

    user = models.OneToOneField(User, verbose_name=_(u'user'), related_name="+",
            blank=True, null=True)
    name = models.CharField(_(u"name"), blank=True, max_length=200)
    company_name = models.CharField(_(u"company name"), max_length=100, blank=True)
    email = models.EmailField(_(u"e-mail"), blank=True, db_index=True, max_length=50)
    phone = models.CharField(_(u'phone'), blank=True, db_index=True, max_length=20)
    primary_address = models.ForeignKey(CustomerAddress, verbose_name=_(u'primary address'),
            on_delete=models.SET_NULL, # forgo customer deletion on address deletion!
            related_name="+", blank=True, null=True)
    date_created = models.DateField(_(u'date created'), auto_now_add=True)

    objects = CachingManager(cache_fields=['id',])

    class Meta:
        verbose_name = _(u'customer')
        verbose_name_plural = _(u'customers')

    def __unicode__(self):
        return "%s(%s)" % (self.name, self.email)

    def save(self, **kwargs):
        """
        Propagate changes in user/customer data to related user object
        TODO:
            propagate user.first_name/last_name
        """
        super(Customer, self).save(**kwargs)
        #self.customer.email = self.email
        #self.customer.phone = self.phone
        #self.customer.save()

    def get_active_addresses(self):
        return self.addresses.filter(active=True)

    def is_blank(self):
        """
        Whether customer data is not filled
        If either of fields name,email,phone is not filled, the Customer is blank
        """
        return (self.name == ""
                or self.email == ""
                or self.phone == "")

    @classmethod
    def get_customer(cls, request, force_save=False):
        """
        Get a customer instance for the client based on request and user
        NOTE: this is copypasted from yz.cart.models.Cart.get_cart()
        """
        customer = None
        if cls.SESSION_CUSTOMER_ID in request.session:
            customer_id = request.session[cls.SESSION_CUSTOMER_ID]
            try:
                customer = cls.objects.get_cached(id=customer_id)
            except cls.DoesNotExist:
                pass

        # use the auth-user's last customer ONLY if current session customer is empty
        # `empty` can also mean no items in customer
        if not customer and request.user.is_authenticated():
            try:
                customer = cls.objects.get(user=request.user)
            except cls.DoesNotExist:
                # create new customer instance for the user
                # do not save yet
                customer = cls(user=request.user)

        # create new customer instance if none
        if customer is None:
            customer = cls()

        # force_save a new customer if requested
        if force_save and not customer.id:
            customer.save()

        # update session
        if customer.id:
            request.session[cls.SESSION_CUSTOMER_ID] = customer.id
        else:
            # remove stale customer id if any
            request.session.pop(cls.SESSION_CUSTOMER_ID, None)
        return customer

    @classmethod
    def get_or_create_customer(cls, request):
        return cls.get_customer(request, force_save=True)
