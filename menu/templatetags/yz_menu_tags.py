# -*- coding: utf-8 -*-
"""
Menu tags:
using filter chain:
{% with menu_items=menu_group:"Some Menu Group"|menu_items:False %}
    {% display_menu menu_items current_menu_item 'my/menu/template' %}
{% endwith %}

"""
from __future__ import unicode_literals
import logging
from django import template
from django.template.loader import render_to_string

from yz.utils.tree import create_tree_from_list
from yz.menu.models import MenuGroup

register = template.Library()

logger = logging.getLogger('default')

@register.simple_tag
def yz_menu(name, template_name='menu/menu.html'):
    """
    """
    menu_group = MenuGroup.objects.get_cached(name=name)
    menu = menu_group.get_active_items()
    return render_to_string(template_name, {"menu": menu})

@register.inclusion_tag('menu/main-menu.html')
def main_menu():
    """
    Display main menu (the menu items from the 1st group, top-level only)
    """
    menu_group = MenuGroup.objects.get_cached(id=1)
    menu = menu_group.get_active_items()
    return {
        'main_menu': menu,
    }

@register.filter
def menu_group(name):
    """
    Get a menu group
    @param name: the name
    @return: MenuGroup instance
    """
    return MenuGroup.objects.get_cached(name=name)

@register.filter
def menu_items(menugroup, active=True):
    """
    @param menugroup: MenuGroup instance
    @param active: whether to get only active items vs. all
    @return: CacheProxy
    """
    active = active or None  # force None to prevent active=False ;-)
    return menugroup.get_items(active=active)

@register.filter
def menu_tree(items, cached=True):
    """
    @param items: CacheProxy
    @param cached: whether to use cache
    @return: yz.utils.tree.RootNode instance
    """
    items_list = items.cached if cached else items.uncached
    return create_tree_from_list(items_list)

@register.simple_tag
def display_menu_tree(menu_tree_node, current=None, template_name='menu/tags/display-menu-tree.html'):
    context = {
        'menuitem': menu_tree_node,
        'current': current,
        'template_name': template_name,  # easing the recursion
    }
    return render_to_string(template_name, context)

@register.simple_tag
def display_menu(items, current=None, template_name='menu/tags/display-menu.html'):
    context = {
        'menuitems': items.cached,
        'current': current,
        'template_name': template_name,  # easing the recursion
    }
    return render_to_string(template_name, context)

