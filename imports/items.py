# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('exports')

from django.utils.encoding import StrAndUnicode
#from django.utils.text import slugify
from yz.utils import translit
from yz.utils import translit_and_slugify

class Item(StrAndUnicode):
    """
    Abstract Item
    Property access rules:
    - missing properties are looked up by __getattr__()
    - missing properties beginning with "_" will raise AttributeError immediately to avoid infinite recursion
    - property name can be specified in class variables tags and attrs:
        - `tags` is a map of property names to child nodes' nodeName's (taking the node's text value)
        - `attrs` is a map of property names to node's attributes
        - the lookup is done by _get_attr() method
        - if property not found, AttributeError is raised
    - by default, the raw (unicode) value of the node/attribute is returned (the behavior of _get_attr())
    - class variable `property_adjust` is a map of property names to functions used to adjust _get_attr() values
        - if the adjust function fails, ... ### TODO ###
    - available property values are cached in __dict__ under "_" prefix
    - of course, override all this by @property

    """

    tags = dict(id = u"id")
    attrs = dict()
    property_adjust = {}

    def __init__(self, node):
        self.node = node

    def __unicode__(self):
        try:
            return u"%s (%s)" % (self.name, self.id)
        except AttributeError:
            return u"<noname> (%s)" % self.id

    def __getattr__(self, attr):
        """
        Implement attribute caching
        """
        if attr[0] == "_":
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))
        # search for a cached attribute
        _saved_attr = "_%s" % attr
        # ### old: we don't want to eval self._get_attr(attr) each time
        # return self.__dict__.setdefault(_saved_attr, self._get_attr(attr))
        try:
            return self.__dict__[_saved_attr]
        except KeyError:
            val = self._get_attr(attr)
            try:
                adjust = self.property_adjust[attr]
            except KeyError:
                pass
            else:
                val = adjust(val)
            self.__dict__[_saved_attr] = val
            return val


    def _get_attr(self, attr):
        """ Get attribute given by either an XML tag or XML attribute of the item's node """
        # search for a tag
        _tag = self.tags.get(attr)
        if _tag is None:
            # search for an attribute
            _attr = self.attrs.get(attr)
            if _attr is None:
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))
            else:
                val = self.node.getAttribute(_attr)
        else:
            val = self._get_tag_value(_tag)
        return val


    def _get_tag_value(self, tag_name, direct_child=True):
        """ Get a tag's text value as item's property value
            direct_child: whether to match only direct child or any descendant
        """
        try:
            val = self.node.getElementsByTagName(tag_name)[0]
        except:
            pass
        else:
            if not direct_child or val.parentNode == self.node:
                return self.get_text_node_value(val)
        raise AttributeError(u"%s: '%s' node has no %s tag '%s'" % (
                self.__class__.__name__,
                self.node.tagName,
                "child" if direct_child else "descendant",
                tag_name))

    @staticmethod
    def get_text_node_value(node):
        try:
            textval = node.firstChild
        except AttributeError:
            pass
        else:
            if textval is not None and textval.nodeType == node.TEXT_NODE:
                return textval.data
        return None

    @property
    def id(self):
        if "_id" not in self.__dict__:
            _id = self._get_attr("id")
            try:
                _id = int(_id)
            except:
                _id = None
            self.__dict__["_id"] = _id
        return self._id


class NamedItem(Item):
    "Item with name"

    tags = dict(name = u"name")

    @property
    def name(self):
        if "_name" not in self.__dict__:
            _name = self._get_attr("name")
            if _name == "":
                _name = None
            self.__dict__["_name"] = _name
        return self._name


class SluggedItem(NamedItem):
    "Item with slug auto-derived from name"

    @property
    def slug(self):
        "Create slug from name using translit"
        #name = self._get_tag_value(self.tag_name)
        if "_slug" not in self.__dict__:
            name = self.name
            self.__dict__["_slug"] = translit_and_slugify(name) if name is not None else None
        return self._slug


class ProductItem(SluggedItem):
    "Product item"

    # example
    tags = dict(uuid = u"uuid",
        sku = u"sku",
        price = u"price",
        description = u"description",
        base_product = u"base_product",
        category = u"category",
        categories = u"categories",
        units = u"units",
        quantity = u"quantity",
    )


    @property
    def categories(self):
        """ Multiple categories as multiple category tags under a categories tag
            e.g. <cats><cat>11</cat><cat>12</cat></cats>
        """
        cats = []
        try:
            cat_nodes = self.node.getElementsByTagName(self.tag_categories)[0]
        except IndexError:
            pass
        else:
            for c in cat_nodes.getElementsByTagName(self.tag_category):
                try:
                    cats.append(c.firstChild.nodeValue)
                except:
                    pass
        return cats


class CategoryItem(SluggedItem):
    "Category item"

    # example
    tags = dict(uuid = u"uuid",
        parent = u"parent",
        description = u"description")

    def __init__(self, node):
        self.node = node
        logger.debug(u"%s: CategoryItem(%s)", node.tagName, self.name)

    @property
    def uid(self):
        return self._get_tag_value(self.tag_uuid)


