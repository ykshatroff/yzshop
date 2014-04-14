__author__ = 'yks'


def create_tree_from_list(objects):
    """
    Create a tree from a list of objects whose id and parent id are stored in attributes
    There can be only one root node so an empty root node is created with id 0.
    All nodes with no parent are children of the root node.
    """
    root = RootNode()
    for obj in objects:
        root.create_node(obj, node_id=obj.id, parent_id=obj.parent_id)
    return root


class Node(object):
    """
    A hierarchical tree: root is the root node (can have content or not)

    """
    def __init__(self, root, content, id=None):
        self.content = content
        self.root = root
        self.id = id
        self.children = []
        self.parent = None
        self.level = None  # used in flatten only

    def add_child_node(self, node):
        """ Add
        """
        self.children.append(node)
        node.parent = self

    def remove_child_node(self, node):
        """ remove
        """
        self.children.remove(node)
        node.parent = None

    def flatten_tree(self, level=0):
        self.level = level
        tree = [self]
        for ch in self.children:
            tree.extend(ch.flatten_tree(level+1))
        return tree

    def __iter__(self):
        for node in self.children:
            yield node


class RootNode(Node):
    def __init__(self):
        self.id = None
        self.parent = None
        self.content = None
        self.children = []
        self.root = None
        self._all = {}

    def create_node(self, content, node_id=None, parent_id=None):
        """
        Create a node in the tree from the given content, assign it an id and
            add it as a child to a parent node.
        If a node refers to a parent which does not exist, a ghost node
            for the parent is created with empty content.
            For a valid list (with unique tree IDs and integrity control),
            all ghost nodes would be transformed to normal nodes. If this
            does not happen, ghost nodes and their children will be excluded
            from further processing.
        """
        try:  # check if such a node exists
            node = self._all[node_id]
        except KeyError:
            node = self._all[node_id] = Node(root=self,
                                             content=content,
                                             id=node_id)
        else:  # the node can be a ghost node if it has no content
            if node.content is not None:
                raise ValueError("Node already exists")
            node.content = content

        if parent_id:  # node is a branch node
            try:
                # use already existing parent node
                parent_node = self._all[parent_id]
            except KeyError:
                # create a ghost node (without content)
                parent_node = self._all[parent_id] = Node(root=self,
                                                          content=None,
                                                          id=parent_id)
        else:  # node is a top level node
            parent_node = self
        parent_node.add_child_node(node)
        return node

    def delete_node(self, node, keep_branch=False):
        if node.root != self:
            raise ValueError("Failed to delete: Node is not in the tree")
        del self._all[node.id]
        if node.parent:
            node.parent.remove_child_node(node)
        if keep_branch:
            for ch in node.children:
                ch.parent = None
            node.children = []
        else:  # recursively delete the branch
            for ch in node.children:
                self.delete_node(ch)

    def as_list(self):
        return self.flatten_tree(0)

    def __getitem__(self, item):
        return self._all[item]

