from django.conf.urls.defaults import *
from django.views.generic import DetailView
from django.views.generic import ListView
#from django.conf import settings

# models
from .models import Question

_namespace = 'yz_faq'
_tpl_dir = 'faq'
_paginate_by = 6

# user patterns
urlpatterns = patterns('yz.faq.views',
    url(r'^page/(?P<page_number>\d+)/$', 'page_view', name='%s_page' % _namespace),
    url(r'^(?P<slug>[\w-]+)/$',
            DetailView.as_view(template_name='%s/entry.html' % _tpl_dir,
                    model=Question),
            {},
            name='%s_entry' % _namespace),
    url(r'^ask$', 'ask_question', name='%s_ask_question' % _namespace ),
    url(r'^question-added$', 'question_added', name='%s_question_added' % _namespace ),
    url(r'^$', 'index_view', name='%s_index' % _namespace),
)
