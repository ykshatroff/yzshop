# -*- coding: utf-8 -*-
#
import re
from .utils import slugify

def translit(string):
    return Translit.translit(string)

def translit_and_slugify(string):
    return slugify(translit(string))


class Translit(object):
    """
    Basic transliteration class (using Russian, but extensible)
    """

    # using a list of tuples since dict mapping does not preserve order
    trans_table = (
        (u'ье', u'je'),
        (u'ьё', u'jo'),
        (u'ья', u'ja'),
        (u'ью', u'ju'),
        (u'ъе', u'je'),
        (u'ъё', u'jo'),
        (u'ъю', u'ju'),
        (u'ъя', u'ja'),
        (u'а', u'a'),
        (u'б', u'b'),
        (u'в', u'v'),
        (u'г', u'g'),
        (u'д', u'd'),
        (u'е', u'e'),
        (u'ё', u'jo'),
        (u'ж', u'zh'),
        (u'з', u'z'),
        (u'и', u'i'),
        (u'й', u'j'),
        (u'к', u'k'),
        (u'л', u'l'),
        (u'м', u'm'),
        (u'н', u'n'),
        (u'о', u'o'),
        (u'п', u'p'),
        (u'р', u'r'),
        (u'с', u's'),
        (u'т', u't'),
        (u'у', u'u'),
        (u'ф', u'f'),
        (u'х', u'h'),
        (u'ц', u'c'),
        (u'ч', u'ch'),
        (u'ш', u'sh'),
        (u'щ', u'sch'),
        (u'ъ', u''),
        (u'ы', u'y'),
        (u'ь', u''),
        (u'э', u'e'),
        (u'ю', u'ju'),
        (u'я', u'ja'),
        (u'А', u'A'),
        (u'Б', u'B'),
        (u'В', u'V'),
        (u'Г', u'G'),
        (u'Д', u'D'),
        (u'Е', u'E'),
        (u'Ё', u'Jo'),
        (u'Ж', u'Zh'),
        (u'З', u'Z'),
        (u'И', u'I'),
        (u'Й', u'J'),
        (u'К', u'K'),
        (u'Л', u'L'),
        (u'М', u'M'),
        (u'Н', u'N'),
        (u'О', u'O'),
        (u'П', u'P'),
        (u'Р', u'R'),
        (u'С', u'S'),
        (u'Т', u'T'),
        (u'У', u'U'),
        (u'Ф', u'F'),
        (u'Х', u'H'),
        (u'Ц', u'C'),
        (u'Ч', u'Ch'),
        (u'Ш', u'Sh'),
        (u'Щ', u'Sch'),
        (u'Ъ', u''),
        (u'Ы', u'Y'),
        (u'Ь', u''),
        (u'Э', u'E'),
        (u'Ю', u'Ju'),
        (u'Я', u'Ja'),
    )

    # initialized on first use
    regexp = None
    trans_map = {}

    @classmethod
    def get_regexp(cls):
        """ Create the regexp and character map when first run """
        if cls.regexp is None:
            subst = []
            for (s,r) in cls.trans_table:
                cls.trans_map[s] = r
                subst.append(s)
            # build the regexp: (a|b|c|...)
            r = u'(' + u'|'.join(subst) + u')'
            cls.regexp = re.compile(r)
        return cls.regexp


    @classmethod
    def translit(cls, instr):
        """ Transliterate string, returning a unicode """
        if not isinstance(instr, unicode):
            instr = unicode(instr, 'utf-8')
        newstr = cls.get_regexp().sub(lambda s: cls.trans_map[s.group(0)], instr)
        return newstr

