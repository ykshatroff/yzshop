# -*- coding: utf-8 -*-
""" Filters module: uniform handling of filter arguments and querysets
        (basically for products, but can be utilized with other data)

    GET filter_key=value --> (internal value) --> DB query: filter(some_key=db_value)
                                |                           |
          GET filter_key=V  <---X--> OUTPUT: <Value>        ----> result

    Usage:
        - Filtering:
        1. subclass AbstractFiltering class to include the desired Filter classes
        2. create Filtering object with GET arguments
        3. apply Filtering to a queryset
        - Displaying filtered values and choices:
        1. After filtering, do Filtering.get_filters_display() to get a list of filters
            with their available values for the queryset and the current values if set.

    API:
    Filter object:
        __init__(value): the current value(s) to filter by
        get_current_value(): get the current value(s)
        get_options(queryset): find possible values to be used for filtering
                for the given queryset => a list of Filter objects with "current values" being
                the available options
        apply(queryset): apply available filtering to the given queryset
        get_argument(): the GET argument for the current value(s)
"""
from __future__ import unicode_literals
from django.utils.encoding import StrAndUnicode
from django.db.models import Min, Max
from django.db.models import Q

from yz.utils.utils import import_symbol
from . import settings


def get_filtering_class():
    if settings.FILTERING:
        try:
            return import_symbol(settings.FILTERING)
        except ImportError:
            pass
    return None


class EmptyResultException(ValueError):
    """ An exception similar to StopIteration, raised by apply() when a filter value
        is a fortiori bound to an empty result, to prevent further apply() processing
    """
    pass


class FilterOption(StrAndUnicode):
    """
    Wrapper for filter options:
        - INPUT: GET parameter
        - OUTPUT: display --> __unicode__
        - OUTPUT: database --> to_db
        - OUTPUT: GET parameter --> to_uri
    """
    def __init__(self, value, text=None, is_current=False):
        """
        value is the raw value from a filter
        """
        self.value = value
        self.is_current = is_current
        self.text = text or self.__unicode__()

    def __unicode__(self):
        return unicode(self.value)

    def to_db(self):
        return self.value

    def to_uri(self):
        """
        @return: unicode, not urlencoded
        """
        return self.value

    @classmethod
    def from_uri(cls, value):
        if not isinstance(value, unicode):
            raise TypeError("Wrong value type for %s (expecting unicode)" % cls.__name__)
        if value == "":
            raise ValueError("Empty value for %s (expecting a non-empty unicode)" % cls.__name__)
        return cls(value, is_current=True)

    @classmethod
    def from_db(cls, value):
        return cls(value)

    def __eq__(self, other):
        if self is other:
            return True
        try:
            return self.value == other.value
        except AttributeError:
            return self.value == other


class Filtering(StrAndUnicode):
    """
    The generic filtering logic, relying on filter_classes instances doing their specific jobs.
    NOTE: Overriding this class with filter_classes property containing a list of filters
        provides for as many filter sets as one desires, while having a settings.SETTING
        limits the choice to one set.
    Attributes:
        filter_classes: filters to apply, in the order of appearance
    """
    # class property
    filter_classes = ()
    # class property
    pattern = "filter_%s"
    # instance property
    # filters = None
    # instance property
    # queryset = None

    def __init__(self, queryset, data=None):
        """
        Create a list of filter objects
        Arguments:
            queryset: the initial queryset to filter
            data: a dict (e.g. GET arguments) with entries like filter.{filter-name}: filter_value
            filters: filter classes to use (order important)
            pattern: the pattern for filters' keys in data
        """
        pattern = self.pattern
        self.queryset = queryset
        self.filters = [filter_class(queryset, data, pattern) for filter_class in self.filter_classes]

    def __nonzero__(self):
        """ True if at least one filter is active """
        return any(self.filters)

    def __unicode__(self):
        """ String display """
        return ";".join(unicode(f) for f in self.filters if f)

    def __iter__(self):
        """
        Iterator over current filters
        """
        for f in self.filters:
            yield f

    def __getitem__(self, key):
        """ Simulate dict[key] access to member filters
        @param key: filter name
        @return: filter object
        """
        for f in self.filters:
            if f.name == key:
                return f
        raise KeyError("No filter with the name %s" % key)

    def apply(self, queryset=None, exclude=()):
        """ Refine a queryset by applying current filters """
        queryset = queryset or self.queryset
        try:
            for f in self.filters:
                if f and f.name not in exclude:
                    queryset = f.apply(queryset)
        except EmptyResultException:  # terminate the loop early if a filter says it will yield no results
            queryset = queryset.none()
        return queryset

    def get_query_string_data(self, exclude=()):
        """ Get a list of 2-tuples of GET arguments: (key=current values),
            omitting empty filters and optionally excluding some by name,
            allowing for multiple same keys: urlencode(args, doseq=True)
        """
        qs = []
        for f in self.filters:
            if f and f.name not in exclude:
                pat = self.pattern % f.name
                qs.extend(map(lambda val: (pat, val),
                              f.to_uri()))
        return qs


class BaseAbstractFilter(StrAndUnicode):
    """
    Base class for all filters
    Methods are given as reasonable defaults
    """
    # name: class property, the name of the filter, doesn't change across instances
    #       identifies filter's value in arguments
    name = None
    # option class
    option_class = FilterOption
    pattern = None
    all_options = None  # cache all options

    def __init__(self, queryset, data=None, pattern=None):
        """
        Arguments:
            queryset: initial queryset
            value: current value, if any
        """
        self.key_name = (pattern or self.pattern) % self.name
        self.initial_queryset = queryset

    def __iter__(self):
        """
        get available options for a filter
        """
        opts = self.get_all_options()
        if opts:
            cls = self.__class__
            for v in opts:
                yield cls(v)

    @property
    def title(self):
        """ Display filter's title """
        return self.name

    def get_options(self, queryset):
        """ Get list of available options for a queryset """
        raise NotImplementedError

    def get_all_options(self):
        """
        Get list of available options for the initial queryset
         NOTE: Tempting to make this method cached, but it can't be known how the queryset is obtained
        """
        if not self.all_options:
            self.all_options = self.get_options(self.initial_queryset)
        return self.all_options

    def apply(self, queryset):
        """
        Apply filter to the queryset
        Return the refined queryset
        Example:
            return queryset.filter(**{self.name: self.value})
        """
        raise NotImplementedError

    def to_uri(self):
        raise NotImplementedError

    def __unicode__(self):
        return self.name

    def __nonzero__(self):
        """ True if value is defined """
        return False

    def find_option(self, opt):
        """
        Get a matching FilterOption from list
        @param opt: FilterOption or a raw value
        @return: FilterOption | none
        """
        all_options = self.get_all_options()
        try:
            return all_options[all_options.index(opt)]
        except ValueError:
            return None

    def _get_current_option(self, val):
        """
        Get an option from all_options which matches the value in val
        @param val: unicode; typically a value from GET/POST data
        @return: FilterOption|None
        """
        try:
            opt = self.option_class.from_uri(val)
        except (ValueError, TypeError):
            return None
        else:
            opt = self.find_option(opt)
            if opt:
                opt.is_current = True
            return opt


class AbstractFilter(BaseAbstractFilter):
    """
    Abstract filter class for single value filters
    """
    current_option = None

    def __init__(self, queryset, data=None, pattern=None):
        super(AbstractFilter, self).__init__(queryset, data, pattern)
        val = self.get_filter_value(data)
        if val is not None:
            self.current_option = self._get_current_option(val)

    def get_filter_value(self, data):
        try:
            return data[self.key_name]
        except KeyError:
            return None

    def to_uri(self):
        return self.current_option.to_uri()

    def __unicode__(self):
        return "%s:%s" % (self.name, self.current_option)

    def __nonzero__(self):
        """ True if value is defined """
        return self.current_option is not None


class AbstractMultiOptionFilter(BaseAbstractFilter):
    """
    Abstract filter class for multiple value filters
    """
    current_option_list = None

    def __init__(self, queryset, data=None, pattern=None):
        super(AbstractMultiOptionFilter, self).__init__(queryset, data, pattern)
        values = self.get_filter_values(data)
        self.current_option_list = self._get_current_options(values) if values else []

    def get_filter_values(self, data):
        """
        Get a list of FilterOptions (or self.option_class instance) representing the values
        @param data: request.GET/POST QueryDict or an object with .getlist() method
        @return: list(FilterOption)
        """
        try:
            return data.getlist(self.key_name)
        except AttributeError:
            return []

    def _get_current_options(self, values):
        result = []
        for value in values:
            opt = self._get_current_option(value)
            if opt:
                result.append(opt)
        return result

    def to_uri(self):
        return [opt.to_uri() for opt in self.current_option_list]

    def __unicode__(self):
        return "%s:[%d value(s)]" % (self.name, len(self.current_option_list))

    def __nonzero__(self):
        """ True if value is defined """
        return bool(self.current_option_list)


class AlphabeticalFilter(AbstractFilter):
    name = 'alpha'
    # value is a letter (character)
    # available values are a set of initial characters of items' names

    def apply(self, queryset):
        return queryset.filter(name__istartswith=self.current_option.value)

    def get_options(self, queryset):
        """ Get list of available options
            For this filter, the list of first characters
        """
        if True:
            # ### using database
            qs = queryset.extra(select={'first_char': 'UPPER(LEFT(name,1))'}).order_by('first_char')
            options = qs.values_list('first_char', flat=True).distinct()
        else:
            # ###
            chars = set()
            for obj in queryset:
                try:
                    char = obj.name[0].upper()
                except:
                    pass
                else:
                    chars.add(char)
            options = sorted(chars)
        return map(self.option_class, options)


class ManufacturerFilter(AbstractFilter):
    name = u'manufacturer'
    title = u'manufacturer'

    def get_options(self):
        product_set = self.category.get_product_set()
        product_set = self.filters.apply(product_set, exclude=self)
        # get manufacturers list
        manufacturers = Manufacturer.objects.filter(products__in=product_set.values_list('id'))
        return manufacturers.distinct()


    def apply(self, queryset):
        if not self.filter_value:
            return queryset
        return queryset.filter(manufacturer__name__iexact=self.filter_value)


class PriceFilterOption(FilterOption):
    def __unicode__(self):
        return "%s,%s" % self.value

    @property
    def price_lower(self):
        return self.value[0]

    @property
    def price_upper(self):
        return self.value[1]

    def to_uri(self):
        return "%s,%s" % self.value

    @classmethod
    def from_uri(cls, value):
        try:
            pmin, pmax = value.split(',', 1)
            pmin = int(pmin)
            pmax = int(pmax)
        except:
            raise ValueError("Failed to parse filter value from argument")
        else:
            value = pmin, pmax
            return cls(value)


class PriceFilter(AbstractFilter):
    name = u'price'
    option_class = PriceFilterOption

    def __unicode__(self):
        return "%s:%s" % (self.name, self.current_option)

    @property
    def title(self):
        """ Display filter's title """
        return "Price: %s to %s" % (self.current_option.price_lower, self.current_option.price_upper)

    def get_options(self, queryset):
        qs = queryset.filter(effective_price__gt=0)
        p = qs.aggregate(Min('effective_price'), Max('effective_price'))
        return map(self.option_class,
                   self._get_steps(p['effective_price__min'], p['effective_price__max']))

    def apply(self, queryset):
        return queryset.filter(effective_price__range=self.current_option.value)

    def _get_steps(self, minprice, maxprice):
        if minprice == maxprice:
            steps = [ (minprice, maxprice), ]
        else:
            smin = "%d" % minprice
            smax = "%d" % maxprice
            # leftmost digits
            dmin = int(smin[0])
            dmax = int(smax[0])
            # order of magnitude (power of ten)
            omin = len(smin) - 1
            omax = len(smax) - 1
            if dmin < 5:
                # for price values from 100 to 499.99 (500 exclusive), the step is 500
                start = 5 * (10 ** omin)
                step_mul = 2 # next step is 2 * 500
            else:
                # for price values from 500 to 999.99 (1000 exclusive), the step is 1000
                start = 10 ** (omin + 1)
                step_mul = 5 # next step is 5 * 1000
            if dmax < 5:
                end = 5 * (10 ** omax)
            else:
                end = 10 ** (omax + 1)
            steps = []

            step_min, step_max = 0, start
            while step_max <= end:
                steps.append( (step_min, step_max) )
                step_min, step_max = step_max, step_max * step_mul
                step_mul = 5 if step_mul == 2 else 2
        return steps
