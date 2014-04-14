from django.conf import settings

CURRENCY_FORMAT = getattr(settings, 'YZ_CORE_CURRENCY_FORMAT', "%(value)s %(code)s")
