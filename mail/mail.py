from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from yz.core.models import Shop

def mail_user(email, subject, context, template_name="mail/common.html"):
    """
    Send a mail to the address "email"
    """
    shop = Shop.get_default_shop()

    if isinstance(email, basestring):
        email = [email, ]
    context.update({
        "SHOP": shop,
        })
    subject = u"[%s] %s" % (shop.name, unicode(subject))
    body = render_to_string(template_name, context)
    reply_to = u"%s <%s>" % (shop.name, shop.from_email)
    fail_silently = not settings.DEBUG
    send_mail(subject, body, reply_to, email, fail_silently=fail_silently)

def mail_managers(subject, context, template_name="mail/common.html"):
    """
    Send a mail to the address "email"
    """
    shop = Shop.get_default_shop()
    subject = u"[%s] %s" % (shop.name, unicode(subject))
    context.update({
        "SHOP": shop,
        })
    body = render_to_string(template_name, context)
    reply_to = u"%s <%s>" % (shop.name, shop.from_email)
    #reply_to = get_reply_address()
    fail_silently = not settings.DEBUG
    send_mail(subject, body, reply_to, shop.get_notification_emails(), fail_silently=fail_silently)


def get_shop_name():
    """
    """
    shop = Shop.get_default_shop()
    return shop.name

def get_reply_address():
    """
    """
    shop = Shop.get_default_shop()
    return shop.from_email

def get_admin_emails():
    """
    """
    shop = Shop.get_default_shop()
    return shop.get_notification_emails()
