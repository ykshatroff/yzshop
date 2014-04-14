from __future__ import unicode_literals
# django imports
from django.conf import settings
from django.conf.urls import include, patterns, url
from django.core.urlresolvers import reverse
from django.utils.http import urlencode

urlpatterns = patterns("yz.admin.views",
    url(r'^$', 'index_view', name="yzadmin_index_view"),
    url(r'^(?P<arg>.+)$', 'dispatcher_view', name="yzadmin_dispatcher_view"),
)


def admin_reverse(model_name, action=None, item_id=None, *args, **kwargs):
    """
    Build an admin URL:
     /model_name[/action[/item_id[/arg1[...]]][?kwarg=val...]
    """
    newargs = (model_name, )
    if action:
        newargs += (action, )
    if item_id:
        newargs += (item_id, )

    url = reverse('yzadmin_dispatcher_view', kwargs={
        'arg': '/'.join(str(arg) for arg in newargs+args)
    })
    if kwargs:
        url += "?%s" % urlencode(kwargs)
    return url