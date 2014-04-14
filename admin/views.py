# Create your views here.
from django import http
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache

from .dispatchers import Dispatcher

@never_cache
def login_view(request, template_name="yzadmin/login.html"):
    """
    The yzadmin login view
    """
    if request.user.is_authenticated():
        # permission check in _login_done
        return _login_done(request)

    login_failed = False
    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            logger.debug('yzadmin.login_view(): username="%s"', form.cleaned_data['username'])
            user = authenticate(username=form.cleaned_data['username'],
                        password=form.cleaned_data['password'])
            if user:
                logger.debug('yzadmin.login_view(): Login user "%s"', user)
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


@never_cache
@permission_required('core.manage_shop')
def index_view(request, template_name="yzadmin/index.html"):
    """
    TODO: Show some dashboard
    """
    Dispatcher.init()
    request.in_yzadmin = True
    response = render_to_response(template_name, RequestContext(request, {
        'menu': Dispatcher.get_menu(),

        #"categories": top_categories,
    }))
    return response

@never_cache
@permission_required('core.manage_shop')
def dispatcher_view(request, arg):
    """
    All job is forwarded to the dispatcher
    """
    Dispatcher.init()
    # NOTE: do not set here
    # request.in_yzadmin = True
    # since dispatcher may go outside the YzAdmin ???

    return Dispatcher.process(request, arg)



def _login_done(request, redirect_to=None, template_name="users/ajax-login-done.html"):
    """
    shortcut for login-done
    TODO check user permissions for yzadmin and if none, either 403 or 404 ???
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
