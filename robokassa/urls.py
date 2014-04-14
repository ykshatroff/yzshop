from django.conf.urls import patterns, url
urlpatterns = patterns("yz.robokassa.views",
    url(r'^$', 'dummy_payment_page', name="yz_robokassa_dummy_payment_page"),
    url(r'^verify$', "verify", name="yz_robokassa_verify"),
    url(r'^done$', 'success', name="yz_robokassa_success"),
    url(r'^fail$', 'failure', name="yz_robokassa_failure"),
)
