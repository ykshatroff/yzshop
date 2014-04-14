# django imports
from django.conf import settings
from django.conf.urls import include, patterns, url

_urls = [
    url(r'^$', 'yz.core.views.index_view', name="yz_index_view"),
    (r'^catalog/', include('yz.catalog.urls')),
]

if 'yz.cart' in settings.INSTALLED_APPS:
    _urls.append( (r'^cart/', include('yz.cart.urls')) )
if 'yz.customer' in settings.INSTALLED_APPS:
    _urls.append( (r'^customer/', include('yz.customer.urls')) )
if 'yz.orders' in settings.INSTALLED_APPS:
    _urls.append( (r'^orders/', include('yz.orders.urls')) )



urlpatterns = patterns("", *_urls)
