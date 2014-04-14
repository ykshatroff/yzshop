import logging
logger = logging.getLogger(__name__)

from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed

def on_delete(sender, instance, **kwargs):
    logger.debug("on_delete(%s, %s)", sender, instance)
    try:
        sender.objects.on_delete(instance)
    except AttributeError:
        pass

def on_save(sender, instance, created, **kwargs):
    logger.debug("on_save(%s, %s)", sender, instance)
    try:
        sender.objects.on_save(instance, created)
    except AttributeError:
        pass

def on_m2m_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    The handler of change of many-to-many relationships
    The handler runs on any M2M relation, because it's possible
        for either side of it to be subject to CachingManager
    It doesn't touch any cached instances themselves
    """
    logger.debug("on_m2m_change(%s, %s: %s)", sender, instance, action)
    if action[:4] != "post":
        # do nothing if the signal is not coming after change
        return

    try:
        # first, try to remove cache entries for the instance's model
        sender.objects.on_m2m_change(instance, model)
    except AttributeError:
        pass

    try:
        # second, try to remove cache entries for the related model
        model.objects.on_m2m_change(instance, sender)
    except AttributeError:
        pass

post_delete.connect(on_delete)
post_save.connect(on_save)
m2m_changed.connect(on_m2m_change)
