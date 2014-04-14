import re
# django imports
from django.db import models
from django.utils.translation import ugettext_lazy as _

from easy_thumbnails.fields import ThumbnailerImageField

from yz.cache.managers import CachingManager
from .managers import StaticBlockManager
from . import settings

class MetaInfoModel(models.Model):
    """
    Abstract model with HTML meta attributes
    This class asserts that a concrete model have a "name" field
    """

    meta_title = models.CharField(_(u"meta title"), max_length=100, default="<name>")
    meta_keywords = models.TextField(_(u"meta keywords"), blank=True)
    meta_description = models.TextField(_(u"meta description"), blank=True)

    class Meta:
        abstract = True


    def get_meta_title(self):
        """ the meta title
        """
        return self.meta_title.replace("<name>", self.name)

    def get_meta_keywords(self):
        """ the meta keywords
        """
        return self.meta_keywords.replace("<name>", self.name)

    def get_meta_description(self):
        """ the meta description
        """
        return self.meta_description.replace("<name>", self.name)


class PositionModelMixin(object):

    def position_down(self):
        return

    def position_up(self):
        return

    def position_first(self):
        return

    def position_last(self):
        return


class Country(models.Model):
    """
    List of countries
    TODO: connect with django-countries

    Fields:
        id : numeric code as per Russian classification of countries of the world (OKSM)
        code : ISO 3166-1 alpha-2 2-letter code
        name : hmmm
    """
    code = models.CharField(_(u"country code"), max_length=2, unique=True)
    name = models.CharField(_(u"name"), max_length=100)

    objects = CachingManager(cache_fields=['id',], timeout=86400)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'country')
        verbose_name_plural = _(u'countries')
        ordering = ("name", )

class Currency(models.Model):
    """
    Currency which can be used for shop pricing

        id: numeric code as per ISO 4217
        code : ISO 4217 3-letter code
    """

    country = models.ForeignKey(Country, verbose_name=_(u"country"), related_name="currencies")
    code = models.CharField(_(u"currency code"), max_length=3, unique=True)
    name = models.CharField(_(u"name"), max_length=100)
    display_format = models.CharField(_(u"display format"), max_length=100,
            default=settings.CURRENCY_FORMAT)

    objects = CachingManager(cache_fields=['id',], timeout=86400)


    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'currency')
        verbose_name_plural = _(u'currencies')
        ordering = ("code", )

    def format(self, value):
        """ Format currency value as per the display_format specified """
        fmt = {
            'code': self.code,
            'value': value,
        }
        try:
            out = self.display_format % fmt
        except:
            out = settings.CURRENCY_FORMAT % fmt
        return out

class StaticBlock(models.Model):
    """
    A block of static HTML which can be assigned to content objects.

    **Attributes**:

    name
        The name of the static block.

    text
        The static HTML of the block.

    """
    name = models.CharField(_(u"name"), max_length=30)
    html = models.TextField(_(u"text"), blank=True)

    # cache entries for the related objects
    objects = StaticBlockManager()


    class Meta:
        ordering = ("name", )
        verbose_name = _(u'static block')
        verbose_name_plural = _(u'static blocks')

    def __unicode__(self):
        return self.name


class Shop(MetaInfoModel):
    """Holds all shop related information.

    Instance variables:

    - name
       The name of the shop. This is used for the the title of the HTML pages

    - shop_owner
       The shop owner. This is displayed within several places for instance the
       checkout page

    - from_email
       This e-mail address is used for the from header of all outgoing e-mails

    - notification_emails
       This e-mail addresses are used for incoming notification e-mails, e.g.
       received an order. One e-mail address per line.

    - description
       A description of the shop

    - image
      An image which can be used as default image if a category doesn't have one

    - google_analytics_id
       Used to generate google analytics tracker code and e-commerce code. the
       id has the format UA-xxxxxxx-xx and is provided by Google.

    - ga_site_tracking
       If selected and the google_analytics_id is given google analytics site
       tracking code is inserted into the HTML source code.

    - ga_ecommerce_tracking
       If selected and the google_analytics_id is given google analytics
       e-commerce tracking code is inserted into the HTML source code.

    - countries
       Selected countries will be offered to the shop customer tho choose for
       shipping and invoice address.

    - default_country
       This country will be used to calculate shipping price if the shop
       customer doesn't have select a country yet.

    """
    name = models.CharField(_(u"name"), max_length=30)
    shop_owner = models.CharField(_(u"shop owner"), max_length=100, blank=True)
    address = models.TextField(_(u"address"), blank=True)
    phones = models.TextField(_(u"phones"), blank=True)
    domain = models.CharField(_(u"domain"), max_length=100, blank=True)
    from_email = models.EmailField(_(u"From e-mail address"))
    notification_emails = models.TextField(_(u"notification email addresses"),
            help_text=_(u'Email addresses separated by comma or one per line'))

    description = models.TextField(_(u"description"), blank=True)
    image = ThumbnailerImageField(_(u"image"), upload_to="images/shop", blank=True, null=True)
    static_block = models.ForeignKey(StaticBlock, verbose_name=_(u"static block"),
            blank=True, null=True, related_name="+")

    google_analytics_id = models.CharField(_(u"Google Analytics ID"), blank=True, max_length=20)
    ga_site_tracking = models.BooleanField(_(u"Google Analytics Site Tracking"), default=False)
    ga_ecommerce_tracking = models.BooleanField(_(u"Google Analytics E-Commerce Tracking"), default=False)

    shipping_countries = models.ManyToManyField(Country, verbose_name=_(u"Shipping countries"), related_name="+")
    default_country = models.ForeignKey(Country, verbose_name=_(u"default country"), related_name="+")

    default_currency = models.ForeignKey(Currency, verbose_name=_(u"default currency"), related_name="+")

    objects = CachingManager(cache_fields=['id',], timeout=86400)

    class Meta:
        permissions = (("manage_shop", "Manage shop"),)
        verbose_name = _(u'shop')
        verbose_name_plural = _(u'shops')

    def __unicode__(self):
        return self.name


    @classmethod
    def get_default_shop(cls, request=None):
        """
        TODO select a shop based on request Accept-Language, locale etc
        """
        return cls.objects.get_cached(id=1)


    def get_default_country(self):
        """Returns the default country of the shop.
        """
        #default_country = self.default_country
        default_country = Country.objects.get_cached(id=self.default_country_id)

        return default_country


    def get_default_currency(self):
        """Returns the default currency of the shop.
        """
        default_currency = Currency.objects.get_cached(id=self.default_currency_id)

        return default_currency


    def get_notification_emails(self):
        """Returns the notification e-mail addresses as list
        """
        addresses = re.split("[\s,]+", self.notification_emails)
        return addresses

    def phones_list(self):
        return re.split("[\n,]+", self.phones)

