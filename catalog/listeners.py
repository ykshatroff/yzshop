import logging
logger = logging.getLogger("default")

#from django.db.models.signals import post_delete
from django.db.models.signals import post_save
#from django.db.models.signals import m2m_changed

from .models import Product
from .models import Property
from .models import ProductPropertyValue
from .signals import product_viewed
from . import settings

def on_product_visited(sender, **kwargs):
    logger.debug("on_product_visited(%s)", sender)
    request = kwargs['request']
    products_visited_list = request.session.get('products_visited', [])
    try:
        # remove old visits: actually at most one last visit, since
        # we remove them each next time
        products_visited_list.remove(sender.id)
    except:
        pass
    products_visited_list.append(sender.id)
    request.session['products_visited'] = products_visited_list

if settings.PRODUCTS_TRACK_VISITED:
    product_viewed.connect(on_product_visited, dispatch_uid="on_product_visited")

### ###
#
### ###

def on_property_updated(sender, instance, created, **kwargs):
    """
    When a property is updated, delete all property values whose type
    does not match the property's type.
    """
    logger.debug("on_property_updated(%s, created=%s)", instance, created)
    if not created:
        prop_values = ProductPropertyValue.objects.filter(property=instance)
        prop_values.exclude(value_type=instance.value_type).delete()

post_save.connect(on_property_updated,
                  sender=Property,
                  dispatch_uid="on_property_updated_delete_stale_values")
