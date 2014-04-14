from django.conf.urls import patterns, url
urlpatterns = patterns("yz.customer.views",
    url(r'^$', 'customer_account', name="yz_customer_account"),
    url(r'^login$', "customer_login", name="yz_login"),
    url(r'^logout$', "customer_logout", name="yz_logout"),
    url(r'^register$', 'customer_register', name="yz_register"),
    url(r'^password-change$', "customer_password_change", name="yz_password_change"),
    url(r'^password-changed$', "customer_password_changed", name="yz_password_changed"),
    url(r'^password-recover$', "customer_password_recover", name="yz_password_recover"),
    url(r'^password-recovered$', "customer_password_recovered", name="yz_password_recovered"),
)
