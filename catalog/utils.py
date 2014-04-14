# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

from collections import OrderedDict

from .models import Product, ProductPropertyValue

def get_variants_and_properties(product, current_values={}, active=True):
    """ XXX ### not needed ???? ###
    Get all variants and their property values in format:
    { variant_id: { property_id: [values] } }*
    """
    all_variants = ProductPropertyValue.objects.get_all_variants_properties(product, active=active)
    for prop_id, val in current_values.items():
        # make up a new mapping of variants matching the conditions
        all_variants = {variant_id: variant_data
                        for variant_id, variant_data in all_variants.items()
                        if val in variant_data.get(prop_id, ())}
    return all_variants


def get_property_filters(product, data):
    """ Given a dict with keys = property slugs and values = strings,
        return a map {property_id: adjusted value}
        based on product's properties
    """
    filters = {}
    props = product.get_properties()
    for prop in props:
        try:
            filter_var = data[prop.slug]
        except KeyError:
            pass
        else:
            #logger.debug("filter_var[%s]=%s", prop.slug, filter_var)
            try:
                filters[prop.id] = prop.value_from_string(filter_var)
            except ValueError:
                pass
    return filters


def find_variant_by_properties(product, filter_values):
    """
    Try to find product's variant by given property values
    (map property_id: value}, @see get_property_filters)
    If not found, raise Product.DoesNotExist
    """
    all_variants = get_variants_and_properties(product, filter_values)
    if not all_variants:
        raise Product.DoesNotExist
    variant_id = all_variants.keys()[0]
    return Product.objects.get_cached(id=variant_id)


def group_by_base_products(product_queryset):
    """ Make a list of products grouped by base_product, in order of appearance
        NOTE: we are not showing base products, rather the first variant in list
    @param product_queryset:
    @return: list( tuple(base_product, list[variants])* )
    """
    result = OrderedDict()  # preserve order
    for product in product_queryset:
        if product.parent_id is None:  # if standalone: TODO not supported now
            result[product.id] = [product]  # `base product` is the product itself
        else:
            variants = result.setdefault(product.parent_id, [])
            variants.append(product)
    return result.values()

