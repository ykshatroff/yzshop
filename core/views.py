import logging

from django import http
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

def index_view(request, template_name="index.html"):
    """
    The index view
    """
    logger = logging.getLogger("default")
    logger.debug("index_view()")
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

