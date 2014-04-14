import logging
from decimal import Decimal as D
import md5
from django.conf import settings
from django.utils.http import urlquote, urlencode
from yz.orders.models import Order

from .errors import *

# test configuration validity on initialization
try:
    rk_args = settings.YZ_ROBOKASSA
except AttributeError:
    raise RobokassaConfigError("Missing robokassa configuration")
else:
    try:
        rk_login = rk_args['LOGIN']
    except AttributeError:
        raise RobokassaConfigError("Bad robokassa configuration: missing LOGIN")

def get_payment_url(order):
    """
    """
    args = {
        'MrchLogin':    rk_login,
        'sCulture':     'ru',
        'OutSum':       order.total,
        'InvId':        order.id,
        'Desc':         'Order_%s' % order.number,
        # to calculdate md5, we need PASS_1 (remove it later)
        'pass1':        rk_args.get("PASS_1"),
    }

    # calculate md5
    m = md5.new()
    m.update("%(MrchLogin)s:%(OutSum)s:%(InvId)s:%(pass1)s" % args)

    # save md5 to args
    args['SignatureValue'] = m.hexdigest()
    # delete pass1
    del args['pass1']

    url = rk_args.get("URL", "https://merchant.roboxchange.com/Index.aspx")

    url = "%s?%s" % (url, urlencode(args))
    return url

def verify_payment(post_data, step=1):
    """
    step is the verification step:
        1 => verify order existence and correct price
        2 => order is paid (user redirected to SUCCESS page)
    """
    logger = logging.getLogger('payments')

    try:
        price   =   post_data['OutSum']
        number  =   post_data['InvId']
        md5     =   post_data['SignatureValue']
    except KeyError:
        logger.exception("robokassa.verify_payment(): bad input data (missing arguments)")
        raise RobokassaDataError("bad input data (missing arguments)")

    logger.info("robokassa.verify_payment(): Order #%s: %s", number, price )

    md5_valid = checksum(number, price, step)

    if md5_valid != md5.upper():
        logger.error("robokassa.verify_payment(): Bad checksum for order #%s: got %s, need %s", number, md5, md5_valid)
        raise RobokassaChecksumError("Bad checksum for order #%s" % number)

    try:
        order = Order.objects.get(id=number)
    except Order.DoesNotExist:
        logger.error("robokassa.verify_payment(): order #%s not found", number)
        raise RobokassaDataError("Order #%s does not exist" % number)

    try:
        in_price = D(price)
    except:
        logger.error("robokassa.verify_payment(): Bad order price '%s'", price)
        raise RobokassaDataError("Bad price '%s'" % price)

    if in_price != order.total:
        logger.error("robokassa.verify_payment(): Price '%s' doesn't match order price %s",
                in_price, order.total)
        raise RobokassaDataError("Price '%s' doesn't match order price '%s'" % (in_price, order.total))

    if not order.is_payable():
        logger.error("robokassa.verify_payment(): Order #%s is not in payable state", order.id)
        raise RobokassaDataError("Order #%s can not be paid (e.g. already paid etc)" % order.id)

    logger.info("robokassa.verify_payment(): SUCCESS: Order #%s verified", order.id)

    return order


def checksum(number, price, step=1):
    """
    generate verification checksum
    step is the verification step:
        1 => need password #2
        2 => need password #1
    """
    if step == 1:
        r_pass = rk_args.get("PASS_2")
    else:
        r_pass = rk_args.get("PASS_1")
    m = md5.new()
    m.update("%s:%s:%s" % (price, number, r_pass) )
    return m.hexdigest().upper()

