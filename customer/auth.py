# django imports
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from yz.customer.models import Customer

import logging
logger = logging.getLogger("default")

class EmailBackend(ModelBackend):
    """Authenticate user by email
    """
    def authenticate(self, username=None, password=None):
        logger.debug("%s.authenticate(email=%s)", self.__class__.__name__, username)
        try:
            user = Customer.objects.get(email=username, user__isnull=False).user
        except (Customer.DoesNotExist, Customer.MultipleObjectsReturned):
            return None
        else:
            if user.check_password(password):
                return user
        return None

class PhoneBackend(ModelBackend):
    """Authenticate user by phone
    """
    def authenticate(self, username=None, password=None):
        logger.debug("%s.authenticate(phone=%s)", self.__class__.__name__, username)
        try:
            user = Customer.objects.get(phone=username, user__isnull=False).user
        except (Customer.DoesNotExist, Customer.MultipleObjectsReturned):
            return None
        else:
            if user.check_password(password):
                return user
        return None
