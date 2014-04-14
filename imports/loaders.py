# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('exports')

from yz.catalog.models import Category
from yz.catalog.models import Product
from yz.catalog.models import ProductVariant

from .readers import Reader
from .readers import ProductReader
from .readers import CategoryReader

class StopLoadingException(Exception):
    pass

class ItemIgnoredException(Exception):
    pass

class Loader(object):
    """ Abstract loader
        Take items from a reader and update them in DB
    """
    object_key = "id"
    update_props = []
    create_props = None
    model = None
    reader = Reader # Abstract!

    def __init__(self):
        pass
        #self.updated_objects = 0
        #self.created_objects = 0

    def load(self, path):
        "Main loading loop"
        reader = self.reader.open(path)
        successful = 0
        total = 0
        updated_objects = 0
        created_objects = 0
        for item in reader.read():
            try:
                is_created = self._load_item(item)
            except StopLoadingException as ex:
                logger.exception("ABORT loading at item '%s': %s", item, ex)
                break
            except ItemIgnoredException as ex:
                logger.debug("IGNORE Item '%s': %s", item, ex)
            except:
                logger.exception("FAILED to load object '%s'", item)
            else:
                successful += 1
                if is_created:
                    created_objects += 1
                else:
                    updated_objects += 1
            total += 1
        logger.info("%s.load(): total '%d', updated %d, created %d; successful %d",
                     self.__class__.__name__,
                     total,
                     updated_objects,
                     created_objects,
                     successful)
        return (total, successful, updated_objects, created_objects)

    def _load_item(self, item):
        """ Load item into DB
            return: True if item was created,
                    False if item was updated
                    if neither, an exception is raised
        """
        obj, is_created = self.fetch_or_create(item)
        self.save(obj, is_created)
        return is_created

    def save(self, obj, is_created):
        obj.save()

    def fetch_object(self, item):
        "Fetch an object from DB based on item's attributes"
        key = getattr(item, self.object_key)
        logger.debug("fetch_object(): key '%s'='%s'", self.object_key, key)
        return self.model.objects.get(**{self.object_key: key})

    def update_object(self, obj, item):
        "Update object by the given list of properties"
        self._copy_item_to_object(item, obj, self.update_props)

    def create_object(self, item):
        "Create object with the given list of properties"
        key = getattr(item, self.object_key)
        obj = self.model(**{self.object_key: key})
        create_props = self.create_props if self.create_props is not None else self.update_props
        self._copy_item_to_object(item, obj, create_props)
        return obj

    def fetch_or_create(self, item):
        """ Find an object in DB by the key given in item
            or create a new object
            Arguments:
                item: the items.Item instance
            Return: tuple (object, is_created) where is_created determines
                whether object was created (True) or found (False)
        """
        key_field = self.object_key
        key = getattr(item, key_field)
        logger.debug("fetch_or_create(): key '%s'='%s'", key_field, key)
        kwargs = {key_field: key}
        try:
            obj = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            obj = self.model(**kwargs)
            props = self.create_props if self.create_props is not None else self.update_props
            is_created = True
            logger.debug("fetch_or_create(): create '%s'='%s'", key_field, key)
        else:
            props = self.update_props
            is_created = False
            logger.debug("fetch_or_create(): update '%s'='%s'", key_field, key)
        self._copy_item_to_object(item, obj, props)
        return (obj, is_created)

    @staticmethod
    def _copy_item_to_object(item, obj, props):
        for prop in props:
            pv = getattr(item, prop)
            setattr(obj, prop, pv)


class ProductLoader(Loader):
    model = Product
    reader = ProductReader
    update_props = ['name']

class CategoryLoader(Loader):
    model = Category
    reader = CategoryReader

    update_props = ['name']
    create_props = ['name', 'slug', ]


