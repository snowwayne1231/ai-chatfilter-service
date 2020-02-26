from pypinyin import pinyin, Style
from ai.models import Vocabulary, SoundVocabulary

import re

g_strict = False
g_heteronym = False
g_tmp_dictionary = {}
g_split_character = '_'
g_pinyin_reg = re.compile('[a-z0-9]+')

def translate_by_string(_string):
    # _words = pinyin(_string, strict=g_strict, style=Style.NORMAL, heteronym=g_heteronym)
    _words = pinyin(_string, strict=g_strict, style=Style.TONE3, heteronym=g_heteronym)

    _words = [_w[0] for _w in _words if g_pinyin_reg.match(_w[0])]

    _next = g_split_character.join(_words) + g_split_character

    return _next


def traceback_by_stringcode(_code):
    _list = g_tmp_dictionary.get(_code, None)

    if _list is None:
        
        _query = SoundVocabulary.objects.filter(pinyin=_code).first()

        if _query:
            _set = _query.vocabulary.values_list('context', flat=True)
            _list = list(_set)
            g_tmp_dictionary[_code] = _list
        else:
            _list = []

    return ','.join(_list)

