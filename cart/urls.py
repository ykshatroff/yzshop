from django.conf.urls import patterns, url
urlpatterns = patterns("yz.cart.views",
    url(r'^$', 'cart_view', name="yz_cart"),
    url(r'^refresh$', 'refresh_cart_view', name="yz_cart_refresh"),
    url(r'^add$', 'add_to_cart_view', name="yz_cart_add_item"),
    url(r'^remove/(?P<id>\d+)$', 'remove_from_cart_view', name="yz_cart_remove_item"),
)
