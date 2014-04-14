from django.conf.urls import patterns, url
urlpatterns = patterns("yz.catalog.views",
    url(r'^$', 'catalog_view', name="yz_catalog"),
    url(r'^search$', 'search_view', name="yz_catalog_search"),
    url(r'^category/(?P<slug>[\w-]+)$', 'category_view', name="yz_catalog_category"),
    url(r'^product/(?P<slug>[\w-]+)$', 'product_view', name="yz_catalog_product"),
)
