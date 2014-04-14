from django.core.urlresolvers import reverse
#from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django import template
register = template.Library()
from ..urls import admin_reverse

@register.simple_tag
def admin_url(model_name, action=None, item_id=None, *args, **kwargs):
    """
    Build an URL for admin console
    """
    return admin_reverse(model_name, action, item_id, *args, **kwargs)

@register.simple_tag(takes_context=True)
def admin_actions_menu(context):
    """
    Output a per-model actions menu
    """
    try:
        dispatcher = context['dispatcher']
    except KeyError:
        return ""
        #pass
    templates = ('yzadmin/%s/actions-menu.html' % dispatcher.name,
                 'yzadmin/actions-menu.html')
    return render_to_string(templates, context)


@register.simple_tag(takes_context=True)
def admin_left_menu(context):
    """
    Output a per-model left menu (pagination etc.)
    """
    try:
        dispatcher = context['dispatcher']
    except KeyError:
        # no left menu at all
        return ""

    try:
        left_menu = dispatcher.get_left_menu(context)
    except AttributeError:
        pass
    else:
        context['left_menu'] = left_menu

    templates = ('yzadmin/%s/left-menu.html' % dispatcher.name,
                 'yzadmin/left-menu.html')
    return render_to_string(templates, context)

@register.simple_tag(takes_context=True)
def admin_include(context, template_name):
    """
    Include an admin template based on current dispatcher
    Construct template path as "yzadmin/%s/%s[.html]" % (dispatcher.name, template_name)
    Fallback to 'yzadmin/defaults/%s.html' % template_name
    """

    if template_name[-5:] == '.html':
        template_name = template_name[:-5]
    templates = 'yzadmin/defaults/%s.html' % template_name

    try:
        dispatcher = context['dispatcher']
    except KeyError:
        # no dispatcher?
        pass
    else:
        templates = ('yzadmin/%s/%s.html' % (dispatcher.name, template_name),
                     templates)

    return render_to_string(templates, context)


@register.inclusion_tag('yzadmin/category/tree-node.html')
def tree_node(category, current=None):
    """
    Recursively render category tree nodes
    Arguments:
        category: a dict {id, name, parent} of category fields
        current: the current category
    """

    return {
        'category': category,
        #'children': category['children'],
        'current': current
    }

@register.inclusion_tag('yzadmin/category/tree-select-node.html', takes_context=True)
def tree_select_node(context, category, selected=None):
    """
    Recursively render category tree nodes with capability
        to select categories
    Arguments:
        category: a dict {id, name, parent} of category fields
        selected: a list of IDs of selected categories
    """

    context.update({
        'category': category,
        'is_current': (selected and category['id'] in selected),
        #'children': category['children'],
        'selected': selected
    })
    return context


@register.simple_tag(takes_context=True)
def admin_page(context, item=None):
    """
    Output per-model pagination
    """
    try:
        dispatcher = context['dispatcher']
    except KeyError:
        # no pages at all
        return ""

    if item is None:
        item = context.get('item')

    try:
        page = dispatcher.get_page(context['request'], item)
    except AttributeError:
        # no pages
        return ""

    context['page'] = page
    context['page_url'] = reverse('yzadmin_dispatcher_view', kwargs={
                'arg': '%s/page' % dispatcher.name
            })
    templates = ('yzadmin/%s/page-block.html' % dispatcher.name,
                 'yzadmin/page-block.html')
    return render_to_string(templates, context)
