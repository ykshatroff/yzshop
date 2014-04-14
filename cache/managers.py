# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.core.cache import cache
from django.db import models
from django.utils.encoding import force_unicode
from hashlib import md5

logger = logging.getLogger(__name__)


class BaseCachingManager(models.Manager):
    """
    BaseCachingManager can be used as base manager class for different managers
    """
    # by default, use the globally configured timeout
    timeout = 3600 * 24
    # preconfigured cache fields
    cache_fields = []
    # per-model prefix (None means default: see add_prefix())
    prefix = None
    # a per-class set of keys (non-prefixed) to be purged on model update
    # initialized on first add
    used_keys = None

    def all_cached(self):
        return self._cache_result( ('all',), self.all )

    def get_cached(self, **kwargs):
        """
        Get a cached instance by field-query, or get it directly from DB backend,
            and then cache the instance if field is in cache_fields
        """
        if len(kwargs) != 1:
            return self.get(**kwargs)

        key_name, key_value = kwargs.items()[0]
        if key_name not in self.cache_fields:
            return self.get(**kwargs)

        cache_key = self._make_cache_key(key_name, key_value)
        cls = self.get_prefix()
        item = self._cache_get(cache_key)
        if item is None:
            logger.debug("%s.get_cached(%s): item not in cache", cls, key_name)
            item = self.get(**kwargs)
            self._cache_set(cache_key, item)
            logger.debug("%s.get_cached(%s): set cache item #%s", cls, key_name, item.pk)
        else:
            logger.debug("%s.get_cached(%s): item in cache", cls, key_name)
        return item

    def on_delete(self, instance):
        """
        On delete signal:
            delete cache entry for the deleted item
        """
        logger.debug("%s.on_delete()", self.get_prefix())
        self._on_update(instance)

    def on_save(self, instance, created):
        """
        On save signal:
            if sending model matches ours,
                delete cache entry for the deleted item
        """
        logger.debug("%s.on_save()", self.get_prefix())
        self._on_update(instance, created)

    # ### Internals ###

    def _cache_result(self, key_tuple, query):
        """
        Get a cached result by a key made up from key_tuple, or execute the query function
            and then cache it
        """
        cache_key = self._make_cache_key(*key_tuple)
        result = self._cache_get(cache_key)
        if result is None:
            result = query()
            self._cache_set(cache_key, result)
        return result

    def _on_update(self, instance=None, created=None):
        """
        Executed on model update signals
        """
        # logger.debug("%s.used_keys:%d", self.get_prefix(), len(self.used_keys))
        if self.used_keys:
            # remove all keys which belong to this model from the used-list
            cache.delete_many(list(self.used_keys))
            # self._cache_del(*self.used_keys)
            # clear used_keys in place, keeping its binding to class/instance
            self.used_keys.clear()

    def _make_cache_key(self, *args):
        """ build key from components
            Components must be encoded so that a different set of
                components not produce the same result
            NOTE: kwargs don't suit because of the importance of the order of args
        """
        key = ",".join(force_unicode(arg) for arg in args).encode('utf-8')
        return "%s:%s" % (self.get_prefix(), md5(key).hexdigest())

    def _cache_get(self, key):
        """ get entry from cache """
        logger.debug("%s._cache_get(%s)", self.get_prefix(), key)
        return cache.get(key)

    def _cache_set(self, key, entry):
        """ set entry to cache
            save_key_to determines where to record the key for later cleanup
                (can be e.g. self.instance_keys)
        """
        cache.set(key, entry, self.timeout)
        logger.debug("%s._cache_set(%s)", self.get_prefix(), key)
        self.save_key(key)

    def _cache_del(self, *args):
        """ delete entries from cache """
        logger.debug("%s._cache_del(%d keys)", self.get_prefix(), len(args))
        cache.delete_many(args)

    @classmethod
    def save_key(cls, key):
        logger.debug("%s.save_key(%s)", cls.__name__, key)
        try:
            cls.used_keys.add(key)
        except AttributeError:
            cls.used_keys = {key}

    def get_prefix(self):
        if self.prefix is None:
            self.prefix = "%s.%s" % (self.model._meta.app_label, self.model.__name__)
        return self.prefix


class CachingManager(BaseCachingManager):
    """
        CachingManager can be used as manager for different models
        CachingManager can be used directly:
            objects = CachingManager(**kwargs)
    """

    def __init__(self, cache_fields=[], timeout=None):
        """
        Set some attributes:
            cache_fields: the models' fields which are used for cache lookups
            timeout: the cache storage timeout
        Ensure that cache keys belong to the manager instance, unique per model,
            rather than the common-for-all BaseCachingManager class
        """
        super(CachingManager, self).__init__()
        cache_fields.extend(self.cache_fields)
        self.cache_fields = cache_fields
        self.timeout = timeout or self.timeout
        # a per-instance used key set
        # explicitly bind used_keys to the Manager's instance (rather than the class)
        self.used_keys = set()

    def save_key(self, key):
        logger.debug("%s.save_key(%s)", self.__class__.__name__, key)
        self.used_keys.add(key)
