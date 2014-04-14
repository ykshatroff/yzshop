#
# import * is safe
#
from django.conf import settings

# whether product variants are used
VARIANTS_ENABLED = getattr(settings, 'YZ_CATALOG_PRODUCTS_VARIANTS_ENABLED', False)

# product price field digits
PRICE_DECIMAL_DIGITS = getattr(settings, 'YZ_CATALOG_PRICE_DECIMAL_DIGITS', 10)
PRICE_DECIMAL_PLACES = getattr(settings, 'YZ_CATALOG_PRICE_DECIMAL_PLACES', 2)

# default ordering of categories on a page in catalog
CATEGORIES_ORDERING = getattr(settings, 'YZ_CATALOG_CATEGORIES_ORDERING', ("position", "name"))

# display subcategories in a category view
CATEGORIES_DISPLAY_CHILDREN = getattr(settings, 'YZ_CATALOG_CATEGORIES_DISPLAY_CHILDREN', True)

# display the complete hierarchy of subcategories in a category view
CATEGORIES_DISPLAY_HIERARCHY = getattr(settings, 'YZ_CATALOG_CATEGORIES_DISPLAY_HIERARCHY', False)

# display products in a category view
CATEGORIES_DISPLAY_PRODUCTS = getattr(settings, 'YZ_CATALOG_CATEGORIES_DISPLAY_PRODUCTS', True)

# display products belonging to all subcategories in a category view
CATEGORIES_DISPLAY_ALL_PRODUCTS = getattr(settings, 'YZ_CATALOG_CATEGORIES_DISPLAY_ALL_PRODUCTS', True)

# the Filtering class to use in a category view
FILTERING = getattr(settings, 'YZ_CATALOG_FILTERING', 'yz.catalog.filters.Filtering')

# the Sorting class to use in a category view
SORTING = getattr(settings, 'YZ_CATALOG_SORTING', 'yz.catalog.sorting.Sorting')

# default ordering of products on a page in catalog
PRODUCTS_ORDERING = getattr(settings, 'YZ_CATALOG_PRODUCTS_ORDERING', ("position", "name"))

# number of products shown on a page in catalog
PRODUCTS_PER_PAGE = getattr(settings, 'YZ_CATALOG_PRODUCTS_PER_PAGE', 10)

# a tuple/list of tab names to disable in yzadmin/product editing
PRODUCTS_ADMIN_TABS_DISABLED  = getattr(settings, 'YZ_CATALOG_PRODUCTS_ADMIN_TABS_DISABLED', None)

# whether to track visited products
PRODUCTS_TRACK_VISITED = getattr(settings, 'YZ_CATALOG_PRODUCTS_TRACK_VISITED', True)
