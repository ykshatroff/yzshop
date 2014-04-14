from django.conf import settings
# default menu creation function (or its Python path)
MENU = getattr(settings, 'YZADMIN_MENU', 'yz.admin.menu.create_menu')
# a tuple of applications to be managed by YzAdmin
MANAGED_APPS = getattr(settings, 'YZADMIN_MANAGED_APPS', settings.INSTALLED_APPS)
