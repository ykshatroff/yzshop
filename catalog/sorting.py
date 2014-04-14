from __future__ import unicode_literals
__author__ = 'yks'
from django.utils.encoding import StrAndUnicode

from yz.utils.utils import import_symbol
from . import settings


def get_sorting_class():
    if settings.SORTING:
        try:
            return import_symbol(settings.SORTING)
        except ImportError:
            pass
    return None


class Sorting(StrAndUnicode):
    """
    TODO: support for multiple sortings at once
    NOTE: multiple sorting=XXX entries in $GET can not guarantee correct ordering
        so use sorting=XXX,YYY ...
    """
    available_sortings = {
        'name': "{desc!s}{sorting}",
        'price': "{desc!s}effective_price",
    }

    def __init__(self, data={}):
        desc = False
        try:
            sorting = data['sorting']
        except KeyError:
            sorting = None
        else:
            if sorting[0] == "-":
                sorting = sorting[1:]
                desc = True
            if sorting not in self.available_sortings:
                sorting = None
        self.sorting = sorting
        self.desc = sorting and desc

    def __unicode__(self):
        return u"%s%s" % ("-" if self.desc else "", self.sorting or "")

    def __nonzero__(self):
        return self.sorting is not None

    def apply(self, queryset):
        if self.sorting is not None:
            s = self.available_sortings[self.sorting].format(
                    sorting=self.sorting,
                    desc="-" if self.desc else "",
                )
            queryset = queryset.order_by(s)
        return queryset

    def opposite(self):
        return Sorting(self.sorting, not self.desc) if self.sorting else self

    def get_available_sortings(self):
        return [Sorting(key) for key in self.available_sortings]
