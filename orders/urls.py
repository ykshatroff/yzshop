from django.conf.urls.defaults import *
from django.views.generic import DetailView
from django.views.generic import ListView
#from django.conf import settings

# models

urlpatterns = patterns('yz.orders.views',
    url(r'^form$', "order_form_view", name='yz_order_form'),
    url(r'^thank-you$', "order_completed_view", name='yz_order_completed'),
)
