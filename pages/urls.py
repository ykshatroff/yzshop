from django.conf.urls.defaults import *
from django.views.generic import DetailView
from django.views.generic import ListView
#from django.conf import settings

# models
from .models import Page

urlpatterns = patterns('',
    url(r'^(?P<slug>[\w-]+)/$',
            DetailView.as_view(template_name='pages/page.html', model=Page),
            {},
            name='yz_page'),
)
