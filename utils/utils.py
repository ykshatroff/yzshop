import re
import sys
import uuid


def slugify(string):
    """ Return a lowercased unicode string with all non-word characters
        replaced with dashes (contiguous dashes removed) """
    if not isinstance(string, unicode):
        string = unicode(string, 'utf-8')
    string = re.sub(u"\W+", u"-", string)
    return string.strip(u"-").lower()


def import_module(module):
    """
    Imports module with given dotted name.
    """
    try:
        module = sys.modules[module]
    except KeyError:
        __import__(module)
        module = sys.modules[module]
    return module


def import_symbol(symbol):
    """
    Imports symbol with given dotted name.
    """
    module_str, symbol_str = symbol.rsplit('.', 1)
    module = import_module(module_str)
    try:
        return getattr(module, symbol_str)
    except AttributeError as e:
        raise ImportError(e.message)

get_uuid = lambda: str(uuid.uuid4())

