# -*- coding: utf-8 -*-
"""
General principles of caching of many-to-many relationships
E.g. products <-> categories
If a product's categories list is changed, both categories-for-product and
    products-for-category cache entries become stale.
Yet, if a product or category changes, the relationship remains, so it requires
    a separate cache holding only the IDs - ProductCategoryRelationManager

"""
import logging
from django.db.models import Model
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.utils.http import urlquote

from yz.cache.managers import BaseCachingManager
from yz.cache.managers import CachingManager
from . import settings


def str_object_ids(object_ids, join_str=','):
    """ Get a string of sorted (integer) IDs, joined by join_str """
    return join_str.join(["%d" % i for i in sorted(object_ids)])


class CategoryManager(BaseCachingManager):

    cache_fields = ['id', 'slug']

    # per-class used_keys
    used_keys = set()

    # track cache keys for products-to-categories relationship
    # to clear them on m2m_changed
    # (on model update, they will be cleared because they are recorded into used_keys)
    products_keys = set()

    def get_all_categories(self, active=True):
        """
        get all categories in a hierarchical tree
        """
        cache_key = self._make_cache_key("all", "active", active)
        tree = self._cache_get(cache_key)
        if tree is None:
            if active:
                # active=False doesn't make sense
                values = self.filter(active=True)
            else:
                values = self.all()
            tree_all = {}
            tree = []
            for cat in values:
                cat.subcategories = []
                tree_all[cat.id] = cat
            for cat in values:
                parent_id = cat.parent_id
                if parent_id:
                    try:
                        tree_all[parent_id].subcategories.append(cat)
                    except KeyError:
                        # parent category may be inactive
                        pass
                else:
                    tree.append(cat)
            self._cache_set(cache_key, tree)
        return tree

    def get_top_categories(self, active=True):
        """
        get the categories whose parent category is none
        """
        cache_key = self._make_cache_key("top_categories",
                "active", active)
        top_cats = self._cache_get(cache_key)
        if top_cats is None:
            top_cats = self.filter(parent=None)
            if active:
                top_cats = top_cats.filter(active=True)
            self._cache_set(cache_key, top_cats)
        return top_cats

    def get_children(self, category, active=True):
        """
        get the child categories for category
        """
        cache_key = self._make_cache_key("children_of", category.id,
                "active", active)
        children = self._cache_get(cache_key)
        if children is None:
            children = self.filter(parent=category)
            if active:
                children = children.filter(active=True)
            self._cache_set(cache_key, children)
        return children


    def get_all_subcategories(self, category, active=True, ids_only=False):
        """
        get a list of all subcategories recursively for a category
        (not including itself)
        Arguments:
            ids_only: return only IDs of found categories in the list
        """
        cache_key = self._make_cache_key("subcategories", category.id,
                                         "active", active,
                                         "ids_only", ids_only)
        result = self._cache_get(cache_key)
        if result is None:
            # first-level children can be taken from cache
            result = []
            tmp_result = self.filter(parent=category)
            if active:
                tmp_result = tmp_result.filter(active=True)
            if ids_only:
                tmp_result = tmp_result.values_list('id', flat=True)
            while tmp_result:
                result.extend(tmp_result)
                # find children of previous level
                tmp_result = self.filter(parent__in=tmp_result)
                if active:
                    tmp_result = tmp_result.filter(active=True)
                if ids_only:
                    tmp_result = tmp_result.values_list('id', flat=True)
            self._cache_set(cache_key, result)
        return result

    def get_ancestors(self, category):
        """
        Get all ancestors of the category, including itself
        """
        cache_key = self._make_cache_key("ancestors_of", category.id)
        ancestors = self._cache_get(cache_key)
        if ancestors is None:
            ancestors = [category]
            while category.parent is not None:
                category = category.parent
                ancestors.append(category)
            ancestors.reverse()
            self._cache_set(cache_key, ancestors)
        return ancestors


    def get_categories_for_product(self, product, active=True):
        """
        The list of categories which the product belongs to
        """
        cache_key = self._make_cache_key("product", product.id, 'active', active)
        categories = self._cache_get(cache_key)
        if categories is None:
            categories = self.filter(products__in=[product])
            if active:
                categories = categories.filter(active=True)
            self._cache_set(cache_key, categories)
            # save key, to clear it on m2m_changed
            self.products_keys.add(cache_key)
        return categories

    def as_tree(self):
        """
        Get the category tree (for menu rendering)
        """
        cache_key = self._make_cache_key("tree")
        tree = self._cache_get(cache_key)
        if tree is None:
            from yz.utils.tree import create_tree_from_list
            values = self.all().only('id', 'parent', 'name')
            tree = create_tree_from_list(values)
            self._cache_set(cache_key, tree)
        return tree

    def as_list(self):
        """
        Get the list of category wrapper objects (for menu rendering)
        Each object contains level
        """
        cache_key = self._make_cache_key("list")
        tree = self._cache_get(cache_key)
        if tree is None:
            tree_all = {}
            tree = []
            values = self.values('id', 'parent_id', 'name')
            for node in values:
                node['children'] = []
                tree_all[node['id']] = node
            for node in values:
                if node['parent_id']:
                    tree_all[node['parent_id']]['children'].append(node)
                else:
                    tree.append(node)
            self._cache_set(cache_key, tree)
        return tree

    def on_m2m_change(self, instance, model):
        """
        Executed on model relationship change signals
        """
        logger = logging.getLogger("default")
        logger.debug("%s.on_m2m_change(%s)", self.model.__name__, model.__name__)

        if model._meta.object_name.lower() == "product":
            # remove all keys which belong to this model from the used-list
            if self.products_keys:
                keys = list(self.products_keys)
                self._cache_del(*keys)
                # clear used_keys in place, keeping its binding to class
                self.products_keys.clear()




class ProductManager(BaseCachingManager):
    """ Manager for Product objects
    """

    cache_fields = ['id', 'slug',]

    # per-class used_keys
    used_keys = set()

    # track cache keys involving Product-to-Category relationship
    categories_keys = set()

    # track cache keys involving Product-to-Property relationship
    properties_keys = set()

    # track cache keys involving Product-to-PropertyValue relationship
    property_values_keys = set()

    @staticmethod
    def _filter_active(product_queryset):
        """ refine product queryset to contain only active products/variants """
        # match all Active products
        qs = product_queryset.filter(active=True)
        if settings.VARIANTS_ENABLED:
            # match ONLY Active variants whose parent is active too
            qs = qs.filter(parent__active=True)
        return qs

    @staticmethod
    def _filter_categories(product_queryset, categories):
        """ refine product queryset to contain only products/variants
            present in the categories list
        """
        if settings.VARIANTS_ENABLED:
            # match ONLY variants whose parent is in categories
            qs = product_queryset.filter(parent__categories__in=categories)
        else:
            qs = product_queryset.filter(categories__in=categories)
        return qs

    def get_variants(self, product, active=True):
        """
        Get the product's variants
        """
        cache_key = self._make_cache_key("variants", product.id,
                                         "active", active)
        variants = self._cache_get(cache_key)
        if variants is None:
            variants = self.filter(parent=product)
            if active:
                variants = variants.filter(active=True)
            self._cache_set(cache_key, variants)
        return variants

    def get_products_in_category(self, category, active=True, deep=False):
        """
        Get the list of products (variants) in a category
        (and its subcategories if deep==True)
        """
        cache_key = self._make_cache_key("category", category.id,
                                         "deep", deep,
                                         "active", active)
        products = self._cache_get(cache_key)
        if products is None:
            categories = [category]
            if deep:
                # get a (cached) list of subcategories from the category object
                categories.extend(category.get_all_subcategories(active=active))
            products = self._filter_categories(self, categories)
            if active:
                products = self._filter_active(products)
            if settings.VARIANTS_ENABLED:  # allow only variants (TODO also standalone products, when supported)
                products = products.exclude(parent=None)

            self._cache_set(cache_key, products)
            if deep:
                # add the cache_key to categories manager
                # to be purged on categories' change
                CategoryManager.save_key(cache_key)
        return products

    def search(self, string,
               sorting=None,  # a Sorting instance
               active=True):

        """ Search products (name and sku) for the string
            Apply paging and sorting
            Search is case-insensitive, with terms separated by space
        """
        string = unicode(string)
        key = urlquote(string)
        cache_key = self._make_cache_key("search", key,
                                         "sorting", sorting,
                                         "active", active)
        match = self._cache_get(cache_key)
        if match is None:
            qs = Q(parent=None)
            # if variants:
            #   TODO
            #   => make a separate query excluding the IDs of products found in the first query
            terms = string.split()
            for term in terms:
                qs &= Q(name__icontains=term)
            qs |= Q(sku__istartswith=string)
            match = self.filter(qs)
            self._cache_set(cache_key, match)
        return match

    def on_m2m_change(self, instance, model):
        """
        Executed on model relationship change signals
        """
        # logger.debug("%s.on_m2m_change(%s)", self.model.__name__, model.__name__)

        obj_type = model._meta.object_name.lower()
        if obj_type == "category":
            # remove all keys which belong to this model from the used-list
            if self.categories_keys:
                keys = list(self.categories_keys)
                self._cache_del(*keys)
                # clear used_keys in place, keeping its binding to class
                self.categories_keys.clear()
        elif obj_type == "property":
            # remove all keys which belong to this model from the used-list
            if self.properties_keys:
                keys = list(self.properties_keys)
                self._cache_del(*keys)
                # clear used_keys in place, keeping its binding to class
                self.properties_keys.clear()
        elif obj_type == "productpropertyvalue":
            # remove all keys which belong to this model from the used-list
            if self.property_values_keys:
                keys = list(self.property_values_keys)
                self._cache_del(*keys)
                # clear used_keys in place, keeping its binding to class
                self.property_values_keys.clear()



class PropertyManager(CachingManager):

    cache_fields = ("id", "slug")

    def get_properties_for_product(self, product):
        """
        TODO
        Get a property for a product from cache
        """
        cache_key = self._make_cache_key("properties_for_product", product.id)
        values = self._cache_get(cache_key)
        if values is None:
            values = self.filter(products__in=[product])
            self._cache_set(cache_key, values)
            ProductManager.properties_keys.add(cache_key)
        return values


    def get_properties_for_category(self, property_id, category, active=None, deep=False):
        cache_key = self._make_cache_key("properties_for_category", category.id)
        values = self._cache_get(cache_key)
        if values is None:
            if deep:
                products = category.get_all_products(active=active)
            else:
                products = category.get_products(active=active)
            values = self.filter(products__in=products)
            self._cache_set(cache_key, values)
            ProductManager.properties_keys.add(cache_key)
        return values


class ProductPropertyValueManager(CachingManager):
    """"""
    def get_all_properties_values(self, product):
        """
        Get the list of all properties' values for a product
        """
        cache_key = self._make_cache_key("product_all_values", product.id)
        values = self._cache_get(cache_key)
        if values is None:
            #logger.debug("get_all_properties_values")
            values = self.filter(product=product).select_related("property", "value_option")
            self._cache_set(cache_key, values)
            ProductManager.property_values_keys.add(cache_key)
            ProductManager.properties_keys.add(cache_key)
        return values

    def get_property_values(self, property, product):
        """
        Get the list of property values for a product
        """
        cache_key = self._make_cache_key("product_property_values", property.id, product.id)
        values = self._cache_get(cache_key)
        if values is None:
            values = self.filter(product=product, property=property)
            if property.is_option:
                field_name = 'value_option__value'
                values = values.select_related("value_option")
            else:
                field_name = property.value_field_name
            values = list(values.values_list(field_name, flat=True).order_by(field_name))
            self._cache_set(cache_key, values)
            ProductManager.property_values_keys.add(cache_key)
            ProductManager.properties_keys.add(cache_key)
        return values

    def get_property_choices(self, property, product, active=True):
        """
        Get the list of variants' distinct property values for a product
        """
        logger = logging.getLogger("default")
        cache_key = self._make_cache_key("product_property_choices", property.id, product.id,
                                         "active", active)
        values = self._cache_get(cache_key)
        if values is None:
            values = self.filter(Q(product=product)|Q(product__parent=product),
                                 property=property)
            if property.is_option:
                field_name = 'value_option__value'
                values = values.select_related("value_option")
            else:
                field_name = property.value_field_name
            values = list(values.values_list(field_name, flat=True).order_by(field_name).distinct())
            self._cache_set(cache_key, values)
            ProductManager.property_values_keys.add(cache_key)
            ProductManager.properties_keys.add(cache_key)
        return values

    def get_all_variants_properties(self, product, active=True):
        """
        Get the mapping of all variants' property values for a product
        The mapping in form { variant_id: { property_id: [values] }}
        """
        cache_key = self._make_cache_key("all_variants_properties", product.id)
        values = self._cache_get(cache_key)
        if values is None:
            res = self.filter(product__parent=product)
            if active:
                res = res.filter(product__active=True)
            res = res.select_related("value_option")
            values = {}
            for ent in res: # ent is a ProductPropertyValue instance
                variant = values.setdefault(ent.product_id, {})
                variant_property_values = variant.setdefault(ent.property_id, [])
                variant_property_values.append(ent.value_option.value if ent.value_option else ent.value)
            self._cache_set(cache_key, values)
            ProductManager.property_values_keys.add(cache_key)
            ProductManager.properties_keys.add(cache_key)
        return values



class ProductImageManager(CachingManager):
    def get_images_for_product(self, product):
        """
        Get the list of images for a product
        """
        cache_key = self._make_cache_key("product", product.id)
        values = self._cache_get(cache_key)
        if values is None:
            values = self.filter(product=product)
            self._cache_set(cache_key, values)
        return values


class ProductCategoryRelationManager(CachingManager):
    pass


class ProductPropertyRelationManager(CachingManager):
    pass

class StockManager(CachingManager):
    def get_stock_for_product(self, product):
        """ Get the total stock number (sum of per-store stock) for a product """
        cache_key = self._make_cache_key("product", product.id)
        stock = self._cache_get(cache_key)
        if stock is None:
            stock = sum(self.filter(product=product).values_list('quantity', flat=True))
            self._cache_set(cache_key, stock)
        return stock
