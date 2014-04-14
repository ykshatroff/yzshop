# -*- coding: utf-8 -*-
import logging

from xml.dom import minidom
from .items import Item
from .items import CategoryItem
from .items import ProductItem


logger = logging.getLogger('exports')

class ReaderException(Exception):
    pass

class Reader(object):
    """
    Abstract reader:
        take an input XML file and produce a list of XML objects

    properties:
    - root_node_name: the name of the node which is the parent of the elements; None is the documentElement
    - entry_node_name: the name of the list entry nodes; None is any node under root_node_name
    - item_class: the class which handles individual list entries
    NOTE: all string values must be unicode strings
    # available get_entry_nodes methods:
    # - get_all_nodes_by_name(tagName)
    # - get_child_nodes()
    # - get_child_nodes_by_name(tagName)
    """

    # settings
    root_node_name = None
    entry_node_name = None
    item_class = Item
    # define which method to use to find entry nodes
    get_entry_nodes = lambda self: self.get_child_nodes()

    # privates
    #_root_node = None
    #_list_entry_nodes = None
    #_documentElement = None

    def __init__(self, documentElement):
        self._documentElement = documentElement

    def read(self):
        """
        Iterator over list entries
        """
        for node in self.get_entry_nodes():
            yield self.item_class(node)

    @classmethod
    def open(cls, path):
        """
        Open an XML document
        """
        try:
            hnd = minidom.parse(path)
        except IOError as ex:
            raise ReaderException("Failed to open file '{}': error '{}'".format(path, ex) )
        return cls(hnd.documentElement)

    def get_root_node(self):
        """
        Get the node which is the parent of the elements;
        based on the root_node_name setting:
            either the name of the node under documentElement,
            or None for the documentElement itself
        """
        try:
            return self._root_node
        except AttributeError:
            if self.root_node_name is not None:
                logger.debug("%s.get_root_node(): root node name %s", self.__class__.__name__, self.root_node_name)
                try:
                    root_node = self._documentElement.getElementsByTagName(self.root_node_name)[0]
                except IndexError:
                    raise ReaderException("Failed to find root node '{}'".format(self.root_node_name) )

            else:
                root_node = self._documentElement
            self._root_node = root_node
            logger.debug("%s.get_root_node(): found %s", self.__class__.__name__, root_node.tagName)
        return self._root_node

    def get_all_nodes_by_name(self, tagName):
        """
        Get the list of all descendant nodes with the tagName
        """
        root_node = self.get_root_node()
        return root_node.getElementsByTagName(tagName)

    def get_child_nodes(self):
        """
        Get the node's child element nodes
        """
        root_node = self.get_root_node()
        entry_nodes = (node for node in root_node.childNodes
                       if node.nodeType == node.ELEMENT_NODE)
        return entry_nodes


    def get_child_nodes_by_name(self, tagName):
        """
        Get the node's child element nodes with tagName
        """
        root_node = self.get_root_node()
        entry_nodes = (node for node in root_node.childNodes
                       if node.nodeType == node.ELEMENT_NODE and node.tagName == tagName)
        return entry_nodes


class ProductReader(Reader):
    """
    Default product reader
    """
    item_class = ProductItem

class CategoryReader(Reader):
    """
    Default category reader
    """
    item_class = CategoryItem
