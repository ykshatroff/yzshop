from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from yz.cache.managers import CachingManager
from yz.catalog.models import Product
from yz.catalog.models import PriceField

def above_zero_validator(value):
    if value <= 0:
        raise ValidationError(_(u'Value must be above zero'))

class CartItem(models.Model):
    """
    CartItem is a distinct stock unit in cart
    NOTE: cart item stores the real selling price of a product at the time of adding to cart
        If the catalog price changes, the cart price remains unchanged.
        But when the cart item is modified, it is updated with the product's current effective_price
    """
    cart = models.ForeignKey("Cart", related_name="items")
    product = models.ForeignKey(Product, related_name="+")
    quantity = models.DecimalField(default=0, max_digits=10, decimal_places=3,
        validators=[above_zero_validator])
    price = PriceField()

    class Meta:
        unique_together = ('cart', 'product')

    def __unicode__(self):
        return "cart %s, product %s: %s*%s" % (self.cart_id, self.product.name, self.price, self.quantity)

    def get_value(self):
        return self.price * self.quantity

# Create your models here.
class Cart(models.Model):
    """
    Cart represents customers' carts
    """
    user = models.ForeignKey(User, related_name="+",
            blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    num_items = models.PositiveIntegerField(default=0)
    value = PriceField(default=0)

    objects = CachingManager(cache_fields=['id',])

    # allow subclasses to use their own session key
    SESSION_CART_ID = 'cart_id'

    class Meta:
        verbose_name = _(u'cart')
        verbose_name_plural = _(u'carts')

    def __iter__(self):
        return iter(self.get_items())

    def __len__(self):
        return self.num_items

    def __nonzero__(self):
        """
        Allow boolean test against cart instances
        """
        return self.num_items > 0

    def __unicode__(self):
        return "cart(%s: %s)" % (self.num_items, self.value)

    @classmethod
    def get_cart(cls, request, force_save=False):
        """
        Get a customer instance for the client based on request and user
        NOTE: this is copypasted to yz.customer.models.Customer.get_customer()
        """
        cart = None
        if cls.SESSION_CART_ID in request.session:
            cart_id = request.session[cls.SESSION_CART_ID]
            try:
                cart = cls.objects.get_cached(id=cart_id)
            except cls.DoesNotExist:
                pass

        # use the auth-user's last cart ONLY if current session cart is empty
        # `empty` can also mean no items in cart
        if not cart and request.user.is_authenticated():
            try:
                cart = cls.objects.get(user=request.user)
            except cls.DoesNotExist:
                # create new cart instance for the user
                # do not save yet
                cart = cls(user=request.user)

        # create new cart instance if none
        if cart is None:
            cart = cls()

        # force_save a new cart if requested
        if force_save and not cart.id:
            cart.save()

        # update session
        if cart.id:
            request.session[cls.SESSION_CART_ID] = cart.id
        else:
            # remove stale cart id if any
            request.session.pop(cls.SESSION_CART_ID, None)
        return cart

    @classmethod
    def get_or_create_cart(cls, request):
        return cls.get_cart(request, force_save=True)

    def get_items(self):
        if self.num_items == 0:
            return []
        return self.items.select_related().all()

    def add_item(self, product, quantity):
        """
        quantity may not be zero/negative
        NOTE: this method may save cart twice
        """
        if not self.id:
            raise ValueError("Can not add to cart: invalid cart")
        quantity = Decimal(quantity) # raises ValueError
        if quantity <= 0:
            raise ValueError("Can not add to cart: invalid quantity")
        try:
            item = self.items.get(product=product)
            item.quantity += quantity
            item.price = product.effective_price
            item.save()
        except ObjectDoesNotExist:
            item = self.items.create(product=product,
                    quantity=quantity,
                    price=product.effective_price)
        self.save()
        return item

    def remove_item(self, item_id):
        """
        Remove item with id=item_id from cart
        If item_id not in cart, raise CartItem.DoesNotExist
        """
        if not self.id:
            raise ValueError("Can not remove from cart: invalid cart")
        self.items.get(id=item_id).delete()
        self.save()

    def refresh(self, data):
        """
        TODO
        """
        items = self.get_items()
        for item in items:
            try:
                q = data["product_%d" % item.id]
            except KeyError:
                item.delete()
            else:
                try:
                    q = Decimal(q)
                except:
                    pass
                else:
                    if q <= 0:
                        item.delete()
                    else:
                        item.quantity = q
                        item.save()
        self.save()

    def clear(self, request):
        """
        Clear cart items
        """
        #self.items.all().delete()
        #self.save()
        try:
            del request.session[self.SESSION_CART_ID]
        except KeyError:
            pass
        self.delete()


    def save(self, *args, **kwargs):
        if self.id:
            # this makes sense only if a cart is not brand-new (i.e. being created)
            # items may have been added/removed
            # caching makes no sense
            my_items = self.items.values_list('price', 'quantity')
            self.num_items, self.value = reduce(
                    lambda s, item: (s[0] + item[1], s[1] + item[0]*item[1]),
                    my_items,
                    (0, 0))
        super(Cart, self).save(*args, **kwargs)

