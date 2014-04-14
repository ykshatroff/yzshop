# -*- coding: utf-8 -*-
"""
Caching decorators for CachingManager methods:
- decorate CachingManager instance methods
- return a proxy object with properties 'cached' and 'uncached'
"""
from __future__ import unicode_literals
from functools import wraps, update_wrapper, WRAPPER_ASSIGNMENTS
from django.utils.encoding import StrAndUnicode

__author__ = 'yks'


class CacheError(Exception):
    pass


class CachingMethodProxy(StrAndUnicode):
    """
    The proxy class provides proxy instances for CachingManager method results.
    Proxying with ``cached`` and ``uncached`` attrs is supported
    """

    def __init__(self, mgr, key, query):
        self.mgr = mgr
        self.key = key
        self.query = query

    @property
    def cached(self):
        return self.mgr._cache_result(self.key, self.query)

    @property
    def uncached(self):
        return self.query()

    def __call__(self, *args, **kwargs):
        return self.query()

    def __unicode__(self):
        return "proxy<%s>" % self.mgr._make_cache_key(self.key)


def cacheable(func):
    """
    To use this decorator, a CachingManager method must return a tuple of the cache key
        and the query function
    @param func: a CachingManager method -> cache_key:tuple, query:function
    @return: wrapper function
    """
    @wraps(func)
    def wrapper(mgr, *args, **kwargs):
        cache_key, query = func(mgr, *args, **kwargs)
        return CachingMethodProxy(mgr, cache_key, query)
    return wrapper


def always_cached(func):
    """
    @TODO
     @always_cached(key_function=key_fn, purge_on_update=bool)...
    @param func: a function to be cached, or a method if additionally decorated with method_decorator
    @return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
