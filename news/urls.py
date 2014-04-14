from django.conf.urls.defaults import *
from django.views.generic import DetailView
from django.views.generic import ListView
#from django.conf import settings

# models
from .models import News

_namespace = 'yz_news'
_tpl_dir = 'news'

# user patterns
urlpatterns = patterns('yz.news.views',
    url(r'^page/(?P<page_number>\d+)/$', 'page_view', name='%s_page' % _namespace),
    url(r'^(?P<slug>[\w-]+)/$',
            DetailView.as_view(template_name='%s/entry.html' % _tpl_dir,
                    model=News),
            {},
            name='%s_entry' % _namespace),
    url(r'^$', 'index_view', name='%s_index' % _namespace),
)
