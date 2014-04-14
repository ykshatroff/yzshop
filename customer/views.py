import logging

from django import http
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from .forms import AuthenticationForm

@login_required
def customer_account(request, template_name="customer/account.html"):
    """
    The customer account data. Only for registered customers
    """
    logger = logging.getLogger("default")
    logger.debug("customer_account()")
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def customer_login(request, template_name="customer/login.html"):
    """
    The customer login view
    """
    logger = logging.getLogger("default")
    logger.debug("customer_login()")
    if request.user.is_authenticated():
        return _login_done(request)

    login_failed = False
    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            logger.debug('customer_login(): username="%s"', form.cleaned_data['username'])
            user = authenticate(username=form.cleaned_data['username'],
                        password=form.cleaned_data['password'])
            if user:
                logger.debug('customer_login(): Login user "%s"', user)
                login(request, user)
                return _login_done(request, redirect_to=request.POST.get("next"))
        login_failed = True
    else:
        form = AuthenticationForm()
    response = render_to_response(template_name, RequestContext(request, {
        "form": form,
        "login_failed": login_failed,
        "redirect_page": request.REQUEST.get("next"),
    }))
    return response

def customer_logout(request):
    """
    The customer login view
    """
    logger = logging.getLogger("default")
    logger.debug("customer_logout()")

    from django.contrib.auth import logout
    logout(request)

    next_view = request.GET.get("next")
    if next_view:
        try:
            next_view = reverse(next_view)
        except:
            next_view = None
    response = http.HttpResponseRedirect(next_view or reverse("yz_index_view"))
    return response

def customer_register(request, template_name="customer/register.html"):
    """
    The customer register view
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def customer_password_change(request, template_name="customer/password_change.html"):
    """
    The customer password_change view
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def customer_password_changed(request, template_name="customer/password_changed.html"):
    """
    The customer password_changed view
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def customer_password_recover(request, template_name="customer/password_recover.html"):
    """
    The customer password_recover view
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def customer_password_recovered(request, template_name="customer/password_recovered.html"):
    """
    The customer password_recovered view
    """
    response = render_to_response(template_name, RequestContext(request, {

    }))
    return response

def _login_done(request, redirect_to=None, template_name="users/ajax-login-done.html"):
    """
    shortcut for login-done
    """
    if request.is_ajax():
        # user is logged in
        response = render_to_response(template_name, RequestContext(request, {
                "user": request.user,
        }))
    else:
        if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
            if request.user.has_perm('core.manage_shop'):
                redirect_to = reverse('yzadmin_index_view')
            else:
                redirect_to = reverse('yz_customer_account')
        response = http.HttpResponseRedirect(redirect_to)
    return response
