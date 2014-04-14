import decimal
import logging
import re

from django import template
from django.http import QueryDict
from django.utils.http import urlencode
from django.utils.html import escape
from django.utils.html import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, page=None):
    """
    Print URL for page switching, preserving GET arguments and
        supplying current item's ID
    """

    url = context.get('page_url', "")
    try:
        request = context['request']
    except KeyError:
        qs = QueryDict()
    else:
        qs = request.GET.copy()
        url = url or request.path

    if page is None:
        page = context.get('page')
    if page is not None:
        qs['page'] = page
    else:
        qs.pop('page', None)

    item = context.get('item')
    try:
        qs['item_id'] = item.pk
    except AttributeError:
        pass

    return "%s?%s" % (url, qs.urlencode())


@register.simple_tag
def highlight(string, term, start_only=False):
    """ Highlight search terms in a string
        Arguments:
            string: a value to process
            term: a space-separated list of search terms
            start_only: whether to match only at the beginning or the whole string
        Highlighting will be done case-insensitively
    """
    logging.debug("highlight('%s','%s')", string, term)
    if not term:
        return string
    if start_only:
        pattern = u'^(%s)' % term
    else:
        terms = u"|".join(re.escape(t) for t in term.split())
        pattern = u'(%s)' % terms
    #regexp = re.compile(pattern, re.I)
    string = escape(string)

    string = re.sub(pattern, u'<b>\\1</b>', string, 0, re.I|re.U)
    #string = regexp.sub(u'<b>\\1</b>', string)
    logging.debug("highlight('%s' =>'%s')", pattern, string)
    return mark_safe(string)
