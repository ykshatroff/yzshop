# django imports
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext

# module imports
from .models import Page
