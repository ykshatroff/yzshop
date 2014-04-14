#import logging

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

#logger = logging.getLogger("default")

class MenuItem(object):
    def __init__(self, name, title, url=None):
        """
        set url to "" to prevent it from being displayed (will be '#'?)
        """
        self.name = name
        self.url = url if url is not None else name
        self.title = title
        self.items = {}
        self.items_ordered = []
        #logger.debug("MenuItem.__init__(%s, %s)", self.name, self.url)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    def add(self, name, title, url=None):
        mi = MenuItem(name, title, url)
        self.items[name] = mi
        self.items_ordered.append(mi)

    def get_item(self, name):
        """ Get a menu item by its path i.e. ancestors' names separated by slashes """
        item = self
        for s in name.split("/"):
            item = item.items[s]
        return item

    def get_items(self):
        return self.items_ordered

    #@models.permalink
    def get_absolute_url(self):
        """
        Returns the absolute_url.
        """
        if self.url == "" or self.url == "#":
            return self.url
        #logger.debug("MenuItem.get_absolute_url(%s, %s)", self.name, self.url)
        return reverse("yzadmin_dispatcher_view", kwargs={"arg": self.url})
        #return ("yzadmin_dispatcher_view", (), {"arg": self.url})

def create_menu():
    """ Create default menu top-level entries """
    # create root menu entry
    menu = MenuItem(None, None)

    # create top-level menu entries
    menu.add('shop', _('Shop'), '#')
    menu.add('catalog', _('Catalog'), '#')
    menu.add('content', _('Content'), '#')
    menu.add('orders', _('Orders'), '#')
    menu.add('other', _('Other'), '#')
    return menu

