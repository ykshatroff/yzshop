# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
# django imports
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from yz.cache.managers import CachingManager
from .managers import MenuItemCachingManager

def get_last_position():
    try:
        last = MenuItem.objects.order_by('-position')[0].position + 10
    except IndexError:
        last = 10
    return last


class MenuGroup(models.Model):
    """Menu group is used for grouping menuitems

    **Attributes**:

    name
        The name of the group.
    """
    name = models.CharField(_(u"name"), max_length=100, unique=True)

    objects = CachingManager(cache_fields=["name"])

    class Meta:
        ordering = ("name", )
        verbose_name = _("menu group")
        verbose_name_plural = _("menu groups")

    def __unicode__(self):
        return self.name

    def get_items(self, active=None):
        """Returns the menuitems of this group.
        """
        return MenuItem.objects.get_items_for_group(self, active=active)

    def get_active_items(self):
        """Returns the active menuitems of this group.
        """
        return MenuItem.objects.get_items_for_group(self, active=True)

    def get_top_level_items(self):
        """Returns the top level (having no parent) menuitems of this group.
        """
        return MenuItem.objects.get_items_for_group(self, top_level=True)


class MenuItem(models.Model):
    """Menu item belongs to a menu group.

    **Attributes**:

    group
        The belonging group.

    title
        The title of the menu tab.

    link
        The link to the object.

    active
        If true the tab is displayed.

    position
        the position of the tab within the menu.

    parent
        Parent tab to create a tree.
    """
    active = models.BooleanField(_(u"active"), default=False)
    title = models.CharField(_(u"title"), max_length=100)
    link = models.CharField(_(u"link"), blank=True, max_length=255,
            help_text=_(u'an absolute link (http://) or a link relative to site root'))
    group = models.ForeignKey(MenuGroup, verbose_name=_(u"group"), related_name="items")
    position = models.IntegerField(_(u"position"), default=1000)
    parent = models.ForeignKey("self", verbose_name=_(u"parent"),
                               related_name="children",
                               blank=True, null=True)
    css_class = models.CharField(_(u"CSS class"), max_length=100, default="", blank=True)

    # allow the menuitem to reference any model's objects
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(db_index=True, blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = MenuItemCachingManager()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """ Get the URL the menu item points to """
        url = self.link
        if re.match(r'[^/:]+://', url):
            return url

        root_url = reverse('yz_index_view')

        return "%s/%s" % (root_url.rstrip("/"), url.lstrip("/"))

    def get_path(self):
        """Get the menu path (cached), including the item itself"""
        return MenuItem.objects.get_path(self)

    def get_children(self):
        """Get the menu item's children"""
        return MenuItem.objects.get_children(self)

    def get_active_children(self):
        """Get the menu path (cached), including the item itself"""
        return MenuItem.objects.get_children(self, active=True)

    class Meta:
        ordering = ("position", )
        verbose_name = _("menu item")
        verbose_name_plural = _("menu items")
