import logging
import locale

from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from .errors import RobokassaError
#from .utils import get_payment_url
from .utils import checksum
from .utils import verify_payment

#@require_POST
def verify(request):
    """
    Called by ROBOKASSA
    """

    if request.method == "POST":
        data = request.POST
    else:
        data = request.GET
    try:
        order = verify_payment(data)
        return HttpResponse("OK%s" % order.id)
    except RobokassaError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseServerError(str(e))


def success(request, template_name="robokassa/success.html"):
    """
    """
    try:
        order = verify_payment(request.GET, step=2)
    except RobokassaError as e:
        return HttpResponseBadRequest(str(e))

    order.set_paid()
    response = render_to_response(template_name, RequestContext(request, {
        "order": order,
    }))
    return response


def failure(request, template_name="robokassa/failure.html"):
    """
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response


def dummy_payment_page(request, template_name="robokassa/dummy.html"):
    """
    """
    from django.conf import settings
    if not getattr(settings, "DEBUG", False):
        raise Http404
    try:
        # use pass Nr.1 to verify
        order = verify_payment(request.GET, step=2)
    except RobokassaError as e:
        return HttpResponseBadRequest(str(e))
    #order = request.session.get("order")
    response = render_to_response(template_name, RequestContext(request, {
        "order": order,
        "md5": checksum(order.id, order.total, step=1) if order else "UNKNOWN",
    }))
    return response
