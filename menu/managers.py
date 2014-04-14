# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from yz.cache.managers import BaseCachingManager
from yz.cache.decorators import cacheable


logger = logging.getLogger("default")


class MenuItemCachingManager(BaseCachingManager):
    """
    """
    timeout = 86400

    @cacheable
    def get_items_for_group(self, group, active=None, top_level=False):
        """
        Get list of items which belong to a group (given as MenuGroup instance or id)
        Use caching
        @param group: MenuGroup instance
        @param active:
        @param top_level:
        """
        cls = self.__class__.__name__
        # an instance or integer ID
        try:
            group = group.id
        except AttributeError:
            group = int(group)

        def query():
            items = self.filter(group=group)
            if active is not None:
                items = items.filter(active=active)
            if top_level:
                items = items.filter(parent=None)
            return items

        cache_key = ("group", group, "active", active, "top_level", top_level)

        return cache_key, query

    @cacheable
    def get_path(self, menuitem):
        """
        Get all ancestors of the menuitem, including itself
        """
        cache_key = ("path_of", menuitem.id)

        def query():
            path = [menuitem]
            while menuitem.parent is not None:
                menuitem = menuitem.parent
                path.append(menuitem)
            path.reverse()
            return path
        return cache_key, query

    @cacheable
    def get_children(self, menuitem, active=None):
        """
        Get children of the menuitem
        """
        cache_key = ("children", menuitem.id)

        def query():
            children = self.filter(parent=menuitem)
            if active is not None:
                children = children.filter(active=active)
            return children
        return cache_key, query
