# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db import models
from django.utils.translation import ugettext_lazy as _

from easy_thumbnails.fields import ThumbnailerImageField

from yz.cache.managers import CachingManager
from yz.core.models import MetaInfoModel
from yz.utils import get_uuid
from yz.utils import translit_and_slugify

from . import settings
from .managers import CategoryManager
from .managers import ProductManager
from .managers import ProductCategoryRelationManager
from .managers import PropertyManager
from .managers import ProductPropertyRelationManager
from .managers import ProductPropertyValueManager
from .managers import ProductImageManager
from .managers import StockManager
from .fields import PriceField
from .fields import OverrideField


class Manufacturer(models.Model):
    """
    Manufacturer
    """
    name = models.CharField(_(u"title"), max_length=100)
    country = models.ForeignKey("core.Country", verbose_name=_(u"country"),
                                blank=True, null=True, related_name="+")
    image = ThumbnailerImageField(_(u"image"), upload_to="images/manufacturers", blank=True, null=True)

    class Meta:
        ordering = ("name", )
        verbose_name = _(u'manufacturer')
        verbose_name_plural = _(u'manufacturers')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.country.name)


class Category(MetaInfoModel):
    """
    Category model with tree-like structure
    NOTE for slug: there can be two approaches to category identification:
            - a slug unique among all categories, which requires some action if there is
                more than one category with a name
            - a slug unique among sibling categories, which requires full path specification
                in a request (URL)
    """
    name = models.CharField(_(u"title"), max_length=100)
    slug = models.SlugField(_(u"slug"), max_length=200, unique=True)
    parent = models.ForeignKey("self", verbose_name=_(u"parent"),
                               blank=True, null=True, related_name="children")
    short_description = models.TextField(_(u"short description"), blank=True)
    description = models.TextField(_(u"description"), blank=True)
    image = ThumbnailerImageField(_(u"image"), upload_to="images/categories", blank=True, null=True)

    position = models.IntegerField(_(u"position"), default=0)
    active = models.BooleanField(_(u"active"), db_index=True, default=False)

    static_block = models.ForeignKey("core.StaticBlock", verbose_name=_(u"static block"),
                                     blank=True, null=True, related_name="+")

    uid = models.CharField(_(u"UUID"), help_text=_(u"Universally unique product ID"),
                           default=get_uuid,
                           max_length=50)

    objects = CategoryManager()

    class Meta:
        ordering = settings.CATEGORIES_ORDERING
        verbose_name = _(u'category')
        verbose_name_plural = _(u'categories')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.slug)

    @models.permalink
    def get_absolute_url(self):
        """
        Returns the absolute_url.
        """
        return "yz_catalog_category", (), {"slug": self.slug}

    @classmethod
    def get_top_categories(cls, active=True):
        """
        Get the (cached) list of top-level categories
        """
        return cls.objects.get_top_categories(active=active)

    def get_children(self, active=True):
        """
        Get the category's children, by default filter out inactive
        Else lookup cached
        """
        return self.__class__.objects.get_children(self, active=active)

    def get_all_subcategories(self, active=True):
        """
        Get the category's subtree, by default filter out inactive
        """
        return self.__class__.objects.get_all_subcategories(self, active=active)

    def get_ancestors(self):
        """
        Get all ancestors of the category, including itself
        """
        return self.__class__.objects.get_ancestors(self)

    def get_products(self, active=True):
        """
        Get products belonging to the category
        """
        return Product.objects.get_products_in_category(self, active=active)

    def get_active_products(self):
        return self.get_products(active=True)

    def get_all_products(self, active=True):
        """
        Get the list of all products (or their IDs if ids_only) which are in
            the category and its subcategories
        """
        product_set = Product.objects.get_products_in_category(self,
                                                               deep=True,
                                                               active=active)
        return product_set

    def get_all_active_products(self):
        return self.get_all_products(active=True)

    # ### not suitable for API
    #def get_manufacturers(self):
        #product_ids = self.get_all_products(active=True, ids_only=True)
        #return Manufacturer.objects.filter(products__in=product_ids).distinct()


class Product(MetaInfoModel):
    """
    Base product class

    """
    UNITS_PIECE = "piece"
    UNITS_PACKAGE = "package"
    UNITS_PAIR = "pair"  # e.g. gloves, socks
    UNITS_SET = "set"
    UNITS_LITER = "l"
    UNITS_METER = "m"
    UNITS_CENTIMETER = "cm"
    UNITS_SQ_METER = "sq.m"
    UNITS_CU_METER = "cu.m"
    UNITS_GRAM = "g"
    UNITS_KILOGRAM = "kg"
    UNITS = (
        (UNITS_PIECE, _(u"piece")),
        (UNITS_PACKAGE, _(u"package")),
        (UNITS_PAIR, _(u"pair")),
        (UNITS_SET, _(u"set")),
        (UNITS_LITER, _(u"l")),
        (UNITS_METER, _(u"m")),
        (UNITS_SQ_METER, _(u"sq.m")),
        (UNITS_CU_METER, _(u"cu.m")),
        (UNITS_GRAM, _(u"g")),
        (UNITS_KILOGRAM, _(u"kg")),
        (UNITS_CENTIMETER, _(u"cm")),
    )

    LENGTH_UNITS = (
        ("m", _(u"m")),
        ("cm", _(u"cm")),
        ("mm", _(u"mm")),
    )
    WEIGHT_UNITS = (
        ("kg", _(u"kg")),
        ("g", _(u"g")),
    )

    # product name is not necessarily unique
    name = models.CharField(_(u"title"), max_length=200)
    variant_name = models.CharField(_(u"variant title"), max_length=200, blank=True)
    # slug is always unique
    slug = models.SlugField(_(u"slug"), max_length=250, unique=True)
    uid = models.CharField(_(u"UUID"), help_text=_(u"Universally unique product ID"),
                           default=get_uuid,
                           unique=True,
                           max_length=50)
    # the base product (when the product is a variant)
    parent = models.ForeignKey('self', verbose_name=_(u"product"),
                               related_name="variants", blank=True, null=True)

    short_description = models.TextField(_(u"short description"), blank=True)
    description = models.TextField(_(u"description"), blank=True)

    position = models.IntegerField(_(u"position"), db_index=True, default=0)
    active = models.BooleanField(_(u"active"), db_index=True, default=False,
                                 help_text=_("whether the product is visible"))

    categories = models.ManyToManyField(Category, verbose_name=_(u"categories"), blank=True,
                                        through="ProductCategoryRelation",
                                        related_name="products")

    manufacturer = models.ForeignKey(Manufacturer, verbose_name=_(u"manufacturer"),
                                     blank=True, null=True, related_name="products")

    # the properties unique for given product / variant
    sku = models.CharField(_(u"SKU"), help_text=_(u"Your unique product article number"),
                           max_length=50, blank=True, null=True, unique=True)
    original_sku = models.CharField(_(u"original SKU"),
                                    help_text=_(u"Manufacturer's product article number"),
                                    blank=True, max_length=50)
    barcode = models.DecimalField(_(u"bar code"), help_text=_(u"EAN-13 or similar bar code"),
                                  blank=True, null=True, max_digits=20, decimal_places=0)

    # package units
    units = models.CharField(_(u"quantity units"), max_length=20, blank=True,
                             choices=UNITS)
    # quantity of items in the product's package measured in package units
    quantity = models.DecimalField(_(u"quantity"), help_text=_(u'quantity per stock unit'),
                                   max_digits=10, decimal_places=3, default=1)

    # price per stock unit (e.g. for a 6-bottle box, the price per box not per each bottle)
    price = PriceField(_(u"price"), blank=True, null=True,
                       help_text=_(u'price per stock unit'))

    on_sale = models.BooleanField(_(u"on sale"), default=False)
    sale_price = PriceField(_(u"sale price"), blank=True, null=True)

    # the price used to sort/filter, calculated as
    # real_sale_price if real_on_sale else real_price
    effective_price = PriceField(_(u"effective price"), editable=False, blank=True, null=True)

    available = models.BooleanField(_(u"available for ordering"), default=True)
    available_date = models.DateField(_(u"when becomes available for ordering"), blank=True, null=True)

    length = models.DecimalField(_(u"length"), blank=True, null=True,
                                 max_digits=10, decimal_places=3)
    width = models.DecimalField(_(u"width"),  blank=True, null=True,
                                max_digits=10, decimal_places=3)
    height = models.DecimalField(_(u"height"), blank=True, null=True,
                                 max_digits=10, decimal_places=3)
    weight = models.DecimalField(_(u"weight"), blank=True, null=True,
                                 max_digits=10, decimal_places=3)

    length_units = models.CharField(_(u"length units"), blank=True,
                                    max_length=3, choices=LENGTH_UNITS)
    weight_units = models.CharField(_(u"weight units"), blank=True,
                                    max_length=3, choices=WEIGHT_UNITS)

    properties = models.ManyToManyField("Property", verbose_name=_(u"properties"),
                                        blank=True,
                                        through="ProductPropertyRelation",
                                        related_name="products")

    # default manager
    objects = ProductManager()

    class Meta:
        ordering = settings.PRODUCTS_ORDERING
        verbose_name = _(u'product')
        verbose_name_plural = _(u'products')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.sku if self.sku is not None else "---")

    @models.permalink
    def get_absolute_url(self):
        """
        Get the absolute url of the product.
        """
        return "yz_catalog_product", (), {"slug": self.slug}

    def save(self, *args, **kwargs):
        """
        Automatically force active=False if both prices are effectively 0
        """
        if self.sale_price <= 0:
            self.sale_price = None
        if self.price <= 0:
            self.price = None
        self.effective_price = self.sale_price if self.on_sale else self.price
        if not self.effective_price:
            self.active = False

        if self.sku == "":
            # need this to avoid unique violation
            self.sku = None

        super(Product, self).save(*args, **kwargs)
        if not self.sku and not self.is_base_product():
            # for base products, it's OK to have no SKU
            self.sku = self.id
            super(Product, self).save(*args, **kwargs)

    def get_parent(self):
        if not self.is_variant():
            return None
        return Product.objects.get_cached(id=self.parent_id)

    @property
    def parent_cached(self):
        """ Unlike get_parent(), raise DoesNotExist if product has no parent """
        return Product.objects.get_cached(id=self.parent_id)

    @property
    def variant_cached(self):
        """ Get a cached instance of ProductVariant
            (cached version of `productvariant` property)
            If product is not a variant, this raises DoesNotExist
        """
        return ProductVariant.objects.get_cached(id=self.id)

    def is_variant(self):
        """Whether the product is a variant of another product"""
        return settings.VARIANTS_ENABLED and self.parent_id > 0

    def is_base_product(self):
        """Whether the product is a base product"""
        return settings.VARIANTS_ENABLED and not self.parent_id

    def get_variants(self, active=None):
        """
        Get the product's variants
        """
        if self.is_variant():
            prod = self.get_parent()
        else:
            prod = self
        variants = Product.objects.get_variants(prod, active)
        return variants

    def get_active_variants(self):
        """
        Get the product's active variants
        """
        return self.get_variants(active=True)

    def get_default_variant(self):
        """ Get Default variant which is either self or the first active variant
        """
        if not settings.VARIANTS_ENABLED:
            return self
        if self.is_variant():
            return self.get_parent().get_default_variant()
        try:
            return self.get_active_variants()[0]
        except IndexError:
            return self

    def get_base_product(self):
        """ Get base product which is either self or the variant's parent (cached)
        """
        return self.get_parent() or self

    def get_categories(self):
        """ Get a cached list of categories the product belongs to """
        prod = self
        if self.is_variant() and not self.variant_cached.own_categories:
            prod = self.get_parent()
        #cat_ids = ProductCategoryRelation.objects.get_categories_for_product(self)
        #return Category.objects.get_categories_by_ids(cat_ids)
        return Category.objects.get_categories_for_product(prod)

    def get_category(self):
        """ Get the first of categories the product is in """
        my_cats = self.get_categories()
        if my_cats:
            return my_cats[0]
        return None

    def in_category(self, category):
        """
        Test whether the product is in a category (using cache)
        Arguments:
            category: Category object, id, or slug
        Returns Category object or None
        """
        my_cats = self.get_categories()
        for cat in my_cats:
            if cat == category or cat.id == category or cat.slug == category:
                return cat
        return None

    def get_images(self):
        """
        Get the list of product's images from cache
        """
        prod = self
        if self.is_variant() and not self.variant_cached.own_images:
            prod = self.get_parent()
        return ProductImage.objects.get_images_for_product(prod)

    def get_image(self):
        """
        Get the product's main image from cache
        """
        try:
            return self.get_images()[0]
        except IndexError:
            return None

    def get_properties(self):
        """Get the list of Property objects for all defined properties """
        prod = self
        if self.is_variant():
            prod = self.get_parent()
        return Property.objects.get_properties_for_product(prod)

    def get_property(self, prop_or_slug):
        if not isinstance(prop_or_slug, Property):
            prop = Property.objects.get_cached(slug=prop_or_slug)
        else:
            prop = prop_or_slug
        if prop in self.get_properties():
            return prop
        raise Property.DoesNotExist("Property '%s' is not defined for product '%s'" % (prop, self))

    def has_property(self, prop_or_slug):
        props = self.get_properties()
        for p in props:
            if p == prop_or_slug or p.slug == prop_or_slug:
                return True
        return False

    def get_property_values(self, prop_or_slug):
        """
        Get the value of a property from cache
        property can be a string (slug) as well as Property instance
        returns the matching property_value object or a list of those
        """
        try:
            prop = self.get_property(prop_or_slug)
        except:
            return None
        val = ProductPropertyValue.objects.get_property_values(prop, self)
        return val

    def get_property_value(self, prop_or_slug):
        val = self.get_property_values(prop_or_slug)
        if val and not prop_or_slug.is_multivalue:
            return val[0]
        return val

    def get_all_properties_values(self):
        """
        Get the list of [variant] product's property values from cache
        """
        return ProductPropertyValue.objects.get_all_properties_values(self)

    def get_property_choices(self, prop_or_slug, active=True):
        """
        Get the list of distinct product's (and its variants') property values from cache
        """
        prod = self.get_parent() or self
        try:
            prop = self.get_property(prop_or_slug)
        except:
            return None
        return ProductPropertyValue.objects.get_property_choices(prop, prod, active=active)

    def get_stock(self):
        return Stock.objects.get_stock_for_product(self)

    def copy(self, **variant_data):
        """
        Copy a variant as a copy of instance, excluding important unique fields
        raises kinda UniqueError
        """
        v = Product(**variant_data)
        for f in ('description',
                  'quantity', 'price', 'on_sale', 'effective_price',
                  'length', 'width', 'height', 'weight'):
            if f not in variant_data:
                setattr(v, f, getattr(self, f))
        v.save()
        for pv in self.property_values.all():
            pv = pv.copy(product=v)
        return v

    def create_variant(self, sku, variant_name, **kwargs):
        if self.is_variant():
            raise ValueError("Cannot add variant to a variant")
        # make up variant's slug as parent's plus add_slug or slugified variant_name
        v = ProductVariant.create(parent=self,
                                  sku=sku,
                                  variant_name=variant_name,
                                  **kwargs)
        return v


class ProductVariant(Product):
    own_name = OverrideField(_(u"title"))
    own_short_description = OverrideField(_(u"short description"))
    own_description = OverrideField(_(u"description"))
    own_manufacturer = OverrideField(_(u"manufacturer"))
    own_price = OverrideField(_(u"price"))
    own_on_sale = OverrideField(_(u"on sale"))
    own_sale_price = OverrideField(_(u"sale price"))
    own_units = OverrideField(_(u"units"))
    own_quantity = OverrideField(_(u"quantity"))
    own_available = OverrideField(_(u"available"))
    own_available_date = OverrideField(_(u"available_date"))
    own_length = OverrideField(_(u"length"))
    own_width  = OverrideField(_(u"width"))
    own_height = OverrideField(_(u"height"))
    own_weight = OverrideField(_(u"weight"))
    own_length_units = OverrideField(_(u"length units"))
    own_weight_units = OverrideField(_(u"weight units"))
    own_categories = OverrideField(_(u"categories"), copy_parent=False)
    own_images = OverrideField(_(u"images"), copy_parent=False)

    objects = CachingManager(cache_fields=['id'])

    class Meta:
        ordering = ('id', )
        verbose_name = _(u'product variant')
        verbose_name_plural = _(u'product variants')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.sku)

    @classmethod
    def create(cls, parent, sku, variant_name, **kwargs):
        """ On create_variant, populate 'own' fields with values from parent """
        slug = kwargs.pop('slug', None)
        if slug is None:
            slug = u"%s-%s" % (parent.slug, translit_and_slugify(variant_name))
        # copy only fields having "own_" counterpart
        fields = (f for f in cls._meta.local_fields
                  if f.name.startswith("own_"))
        for own_field in fields:
            f = own_field.name[4:]
            if f in kwargs:
                kwargs[own_field.name] = True
            elif own_field.copy_parent:
                val = getattr(parent, f)
                kwargs[f] = val
            else:
                pass
        return cls(parent=parent,
                   sku=sku,
                   variant_name=variant_name,
                   slug=slug,
                   **kwargs)

    def copy_parent(self, parent):
        """ Copy parent product's data unless own field is defined """
        field_names = (f.name for f in parent._meta.fields)
        for f in field_names:
            if not getattr(self, "own_%s" % f, True):
                setattr(self, f, getattr(parent, f))

    def is_variant(self):
        return True

    def is_base_product(self):
        return False

    @property
    def variant_cached(self):
        return self


class ProductCategoryRelation(models.Model):
    """
    ProductCategoryRelation defines which categories are assigned to products
        and to their variants if categories_override is off, and controls the order of displaying
        the categories for a product
    """
    product = models.ForeignKey(Product, verbose_name=_(u"product"),
                                related_name="categories_relation")
    category = models.ForeignKey(Category, verbose_name=_(u"category"),
                                 related_name="products_relation")
    position = models.IntegerField(_(u"position"), default=0, db_index=True)

    objects = ProductCategoryRelationManager()

    class Meta:
        ordering = ('position', )
        unique_together = ("product", "category")
        verbose_name = _('Product to Category Relation')
        verbose_name_plural = _('Product to Category Relations')

    def __unicode__(self):
        return "%s:%s(%s)" % (self.product.name, self.category.name, self.position)

    #def save(self, *args, **kwargs):
        #super(ProductCategoryRelation, self).save(*args, **kwargs)
        #m2m_changed.send(sender=Product, instance=self.product, )


class Property(models.Model):
    """
    Property is a multi-purpose class
    The possible uses of Property are: (e.g. for a laptop)
        - product "has property N" (boolean): e.g. LED backlight
        - product has a variant with property N: e.g.
        - product's property N equals ... (or is comparable to ...)
        - set product's property N to ...
    Possible value types are (not limited to):
        - boolean
        - integer
        - option
    """
    VALUE_TYPE_BOOLEAN = u"b"
    VALUE_TYPE_INTEGER = u"i"
    VALUE_TYPE_DECIMAL = u"d"
    VALUE_TYPE_OPTION  = u"o"
    VALUE_TYPE_CHOICES = (
        (VALUE_TYPE_BOOLEAN, _(u"boolean")),
        (VALUE_TYPE_INTEGER, _(u"integer")),
        (VALUE_TYPE_DECIMAL, _(u"decimal")),
        (VALUE_TYPE_OPTION,  _(u"option")),
    )
    VALUE_TYPES = dict([
        (VALUE_TYPE_BOOLEAN, u"boolean"),
        (VALUE_TYPE_INTEGER, u"integer"),
        (VALUE_TYPE_DECIMAL, u"decimal"),
        (VALUE_TYPE_OPTION,  u"option"),
    ])

    name = models.CharField(_(u"title"), max_length=100)
    slug = models.SlugField(_(u"slug"), max_length=100)
    value_type = models.CharField(_(u"value type"), max_length=1, choices=VALUE_TYPE_CHOICES)
    is_multivalue = models.BooleanField(_(u'allow multiple values'), default=False)

    objects = PropertyManager()

    class Meta:
        ordering = ("name", )
        verbose_name = _(u'property')
        verbose_name_plural = _(u'properties')

    def __unicode__(self):
        return self.name

    def get_value_for_product(self, product):
        try:
            val = self.property_values.get(product=product)
        except ProductPropertyValue.DoesNotExist:
            val = None
        else:
            val = val.get_value()
        return val

    @property
    def value_field_name(self):
        """
        The field name to use to access the value of ProductPropertyValue instance
        """
        return "value_%s" % self.VALUE_TYPES[self.value_type]

    @property
    def is_option(self):
        return self.value_type == self.VALUE_TYPE_OPTION

    def value_from_string(self, str_value):
        """
        Parse a string into a value suitable for the Property (coerce to correct type)
        For option-typed Property, return string instead of PropertyOption
        """
        if not isinstance(str_value, unicode):
            raise TypeError("Value must be a unicode")
        if self.value_type == self.VALUE_TYPE_OPTION:
            return str_value
        if self.value_type == self.VALUE_TYPE_DECIMAL:
            val = Decimal(str_value)
        elif self.value_type == self.VALUE_TYPE_INTEGER:
            val = int(str_value)
        elif self.value_type == self.VALUE_TYPE_BOOLEAN:
            val = str_value.lower()
            if val in (u"true", u"on", u"yes", u"1"):
                val = True
            elif val in (u"false", u"off", u"no", u"0"):
                val = False
            else:
                raise ValueError("Failed to parse value for a boolean")
        else:
            raise ValueError("Unknown property type")
        return val


class PropertyOption(models.Model):
    """
    PropertyOption represents textual options
    NOTE: TODO: when saved, update all property_values which use that option
    """
    property = models.ForeignKey(Property, verbose_name=_(u"property"),
                                 related_name="options")
    value = models.CharField(_(u"value"), max_length=100)
    position = models.PositiveSmallIntegerField(_(u"position"), default=0, db_index=True)

    class Meta:
        ordering = ('position', 'value')
        verbose_name = _(u'property option')
        verbose_name_plural = _(u'property options')

    def __unicode__(self):
        return self.value


class ProductPropertyRelation(models.Model):
    """
    ProductPropertyRelation defines which properties are assigned to products
        and must be assigned to their variants, and controls the order of displaying
        the properties
    """
    product = models.ForeignKey(Product, verbose_name=_(u"product"),
                                related_name="properties_relation")
    property = models.ForeignKey(Property, verbose_name=_(u"property"),
                                 related_name="products_relation")
    position = models.IntegerField(_(u"position"), default=10, db_index=True)

    objects = ProductPropertyRelationManager()

    class Meta:
        ordering = ('position', )
        unique_together = ("product", "property")
        verbose_name = _('Product to Property Relation')
        verbose_name_plural = _('Product to Property Relations')

    def __unicode__(self):
        return "%s:%s(%s)" % (self.product.name, self.property.name, self.position)

    def delete(self, *args, **kwargs):
        """
        Automatically delete property values for
            the product's variants
        """
        variants = self.product.get_variants()
        property_values = ProductPropertyValue.objects.filter(product__in=variants,
                                                              property=self.property)
        for pv in property_values:
            pv.delete()  # ensure model's delete() ???
        super(ProductPropertyRelation, self).delete(*args, **kwargs)


class ProductPropertyValue(models.Model):
    """
    ProductPropertyValue is a relation of product_variants to property values
    """
    _property_decorator = property  # for later use

    # Fields
    product = models.ForeignKey(Product, verbose_name=_(u"product"),
                                related_name="property_values")
    property = models.ForeignKey(Property, verbose_name=_(u"property"),
                                 related_name="property_values")
    # this, sort of, violates 2NF
    value_type = models.CharField(_(u"value type"), max_length=1, choices=Property.VALUE_TYPE_CHOICES)

    position = models.IntegerField(_(u"position"), default=10, db_index=True)
    #value = models.CharField(_(u"value"), max_length=100, editable=False)
    value_option = models.ForeignKey(PropertyOption, verbose_name=_(u"property option"),
                                     related_name="property_values", blank=True, null=True)
    value_integer = models.IntegerField(_(u"integer value"), blank=True, null=True, db_index=True)
    value_decimal = models.DecimalField(_(u"decimal value"), blank=True, null=True, db_index=True,
                                        decimal_places=5, max_digits=15)
    value_boolean = models.NullBooleanField(_(u"boolean value"), db_index=True)

    objects = ProductPropertyValueManager()

    class Meta:
        #unique_together = ("product", "property")
        verbose_name = "property value"
        ordering = ('position', )

    def __unicode__(self):
        return u"%d: %d=%s(%s)" % (self.product_id,
                                   self.property_id,
                                   self.get_raw_value(),
                                   self.value_type)

    def __nonzero__(self):
        v = self.get_raw_value()
        return v is not None

    @_property_decorator
    def value_field_name(self):
        """
        The field name to use to access the value of ProductPropertyValue instance
        """
        try:
            return "value_%s" % Property.VALUE_TYPES[self.value_type]
        except:
            # in case of a new ProductPropertyValue instance,
            # self.value_type may not have been set yet
            return self.property.value_field_name

    def get_raw_value(self):
        """
        We assume that a value object can not have any other value set except
            the one for its property's type
        """
        if self.value_option_id is not None:
            return self.value_option_id
        if self.value_integer is not None:
            return self.value_integer
        if self.value_decimal is not None:
            return self.value_decimal
        return self.value_boolean

    def get_value(self):
        """
        Get the real value
        NOTE: a textual value is available even for an Option when cast to string
        """
        return getattr(self, self.value_field_name)

    def set_value(self, value):
        attr = self.value_field_name
        setattr(self, attr, value)

    value = _property_decorator(get_value, set_value)

    @_property_decorator
    def property_cached(self):
        #raise ValueError("property_cached access")
        return Property.objects.get_cached(id=self.property_id)

    def copy(self, **values):
        """
        Create new ProductPropertyValue as a copy of the instance
        """
        pv = ProductPropertyValue(**values)
        for field in self._meta.local_fields:
            f = field.name
            if f not in values:
                setattr(pv, f, getattr(self, f))
        pv.save()
        return pv

    def save(self, **kwargs):
        """ Ensure that a value object has only the value of a proper type
            Not required if the type of property can not be changed
        """
        if not self.value_type:
            # this only should happen on creation, so the property is
            # given explicitly;
            # in case property type changes, all property values should be deleted
            self.value_type = self.property.value_type
        return super(ProductPropertyValue, self).save(**kwargs)


class ProductImage(models.Model):
    """
    """
    product = models.ForeignKey(Product, verbose_name=_(u"product"),
                                related_name="images")
    image = ThumbnailerImageField(_(u"image"), upload_to="images/products")
    position = models.IntegerField(_(u"position"), default=100)
    title = models.CharField(_(u"title"), max_length=200, blank=True)

    objects = ProductImageManager()

    class Meta:
        ordering = ('position', )


# ### Stock and store management ###
class Store(models.Model):
    """
    Represents a store (a sales point or a warehouse)
    """
    TYPE_RETAIL = "r"
    TYPE_WHOLESALE = "w"
    TYPE_INTERNAL = "n"

    TYPE_CHOICES = (
        (TYPE_RETAIL, _(u'retail store')),
        (TYPE_WHOLESALE, _(u'wholesale store')),
        (TYPE_INTERNAL, _(u'internal store')),
    )

    name = models.CharField(_(u"title"), max_length=100, unique=True)
    is_public = models.BooleanField(_(u'whether the store appears on the site'))
    store_type = models.CharField(_(u'store type'), max_length=1, choices=TYPE_CHOICES,
                                  default=TYPE_INTERNAL, db_index=True)

    class Meta:
        ordering = ('name', )
        verbose_name = _(u'store')
        verbose_name_plural = _(u'stores')

    def __unicode__(self):
        return self.name


class Stock(models.Model):
    """
    """
    product = models.ForeignKey(Product, verbose_name=_(u'product'), related_name="stock")
    store = models.ForeignKey(Store, verbose_name=_(u'store'), related_name="stock")
    quantity = models.DecimalField(_(u"quantity"), help_text=_(u'product quantity in stock'),
                                   max_digits=10, decimal_places=3, default=0)

    objects = StockManager()

    class Meta:
        unique_together = ("product", "store")
        verbose_name = _(u'stock')
        verbose_name_plural = _(u'stocks')

    def __unicode__(self):
        return u'%s %d@%d' % (self.quantity, self.product_id, self.store_id)
