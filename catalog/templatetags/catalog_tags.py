import decimal

from django.utils.http import urlencode
from django import template

register = template.Library()

from yz.core.models import Shop
from ..models import Category, Product, ProductPropertyValue
from .. import settings

# price_context = decimal.Context(prec=settings.PRICE_DECIMAL_PLACES)


@register.inclusion_tag('catalog/tags/top-categories.html', takes_context=True)
def top_categories(context):
    """
    Get the top level categories (active only)
    """
    categories = Category.get_top_categories()
    return {
        'top_categories': categories,
        'current_category': context.get('category'),
    }


@register.inclusion_tag('catalog/tags/categories-tree.html', takes_context=True)
def categories_tree(context, category=None, level=0):
    """
    Get the complete hierarchy of categories (active only)
    Use this tag like this:
        - in main template: {% categories_tree %} (w/o args)
        - in categories-tree.html: recurse with args: {%  categories_tree category level %}
    """
    if category is None:
        categories = Category.get_top_categories()
    else:
        categories = category.get_children()

    current_category = context.get('category')
    if current_category:
        current_path = context.get('path', current_category.get_ancestors())
    else:
        current_path = ()
    return {
        'parent': category,
        'categories': categories,
        'level': level + 1,
        'category': current_category,
        'path': current_path,
    }


@register.simple_tag
def make_query_string(page=None, filters=None, sorting=None):
    qs = {}
    if page is not None:
        qs['page'] = page
    if sorting:
        qs['sorting'] = sorting

    if filters:
        qs['filters'] = filters

    return urlencode(qs)


@register.simple_tag(takes_context=True)
def get_price(context, price, decimal_digits=None):
    """
    Display number as price
    Arguments:
        decimal_digits: if None, round to PRICE_DECIMAL_PLACES
                        if int < 0, round to PRICE_DECIMAL_PLACES but avoid all-zeroes
                            (i.e. zeroes after an apparent integer)
                        if int >= 0, round to decimal_digits
    """

    if decimal_digits is None:
        decimal_digits = settings.PRICE_DECIMAL_PLACES
    else:
        decimal_digits = int(decimal_digits)

    try:
        p = decimal.Decimal(price)
    except:
        pass
    else:
        if decimal_digits < 0:
            # try to round to integer
            if int(p) == p:
                p = int(p)
            else:
                decimal_digits = settings.PRICE_DECIMAL_PLACES

        if decimal_digits >= 0:
            # if no rounding to integer took place, ...
            q = '0' * decimal_digits
            p = p.quantize(decimal.Decimal('1.%s' % q))

    try:
        currency = Shop.get_default_shop().get_default_currency()
        p = currency.format(p)
    except:
        pass

    return p


@register.simple_tag
def print_property_value(prop_val):
    """
    Display property value or list of values
    """
    if prop_val:
        if isinstance(prop_val, list):
            text_val = u", ".join(unicode(v.value) for v in prop_val)
        else:
            text_val = prop_val.value
    else:
        text_val = ""
    return text_val


@register.simple_tag
def print_property(prop, variant, not_assigned_text=""):
    """
    Display property value for a product variant
    """
    prop_val = variant.get_property_value(prop)
    if prop_val:
        if isinstance(prop_val, list):
            text_val = u", ".join(unicode(v.value) for v in prop_val)
        else:
            text_val = prop_val.value
    else:
        text_val = not_assigned_text
    return text_val


@register.inclusion_tag('catalog/tags/products-visited.html', takes_context=True)
def products_visited(context, max_number):
    """
    Get the last visited products
    """
    visited_ids = context['request'].session.get('products_visited', [])
    products_visited = []
    for pid in visited_ids[-max_number:]:
        products_visited.append(Product.objects.get_cached(id=pid))
    return {
        'products_visited': products_visited,
    }


@register.assignment_tag
def get_property_choices(product, prop_slug):
    try:
        prop = product.get_property(prop_slug)
    except ValueError:
        # no property -> no value
        return None

    choices = product.get_property_choices(prop)
    return choices


@register.assignment_tag
def get_property_values(product_variants, prop_slug):
    """
    Fetch the list of product's property values (i.e. all distinct values
        of all product's variants) into the context
        Templatetag syntax:
        {% get_property_values product 'my_property' as property_values %}
    """
    product = product_variants[0].get_parent() or product_variants[0]
    try:
        prop = product.get_property(prop_slug)
    except ValueError:
        # no property -> no value
        return None

    property_values = set()
    for product in product_variants:
        property_values.update(ProductPropertyValue.objects.get_property_values(prop, product))
    return property_values


@register.filter
def to_display(products):
    """ Convenience filter to provide both parent and displayed_variant to template
    @param variants: non-empty list of a product's variants
    @return: tuple(parent=product, displayed_variant, variants)
    """
    result = []
    for variants in products:
        displayed_variant = variants[0]
        ent = (displayed_variant.get_parent() or displayed_variant,
               displayed_variant,
               variants)
        result.append(ent)
    return result