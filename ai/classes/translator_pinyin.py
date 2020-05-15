from pypinyin import pinyin, Style
from ai.models import Vocabulary, SoundVocabulary

import re

g_strict = False
g_heteronym = False
g_tmp_dictionary = {}
g_split_character = '_'
g_space = ' '
g_pinyin_reg = re.compile('^[a-zA-Z0-9]+')

def translate_by_string(_string, no_tone=True):
    _tmps = []

    if no_tone:
        _words = pinyin(_string, strict=g_strict, style=Style.NORMAL, heteronym=g_heteronym)
    else:
        _words = pinyin(_string, strict=g_strict, style=Style.TONE3, heteronym=g_heteronym)

    for _w in _words:
        _first_word = _w[0]
        if g_pinyin_reg.match(_first_word):
            _first_word = _first_word.strip()
            if _first_word.find(g_space) >= 0:
                _tmps += _first_word.split(g_space)
            else:
                _tmps.append(_first_word)
    _tmps = [_ for _ in _tmps if _]
    _next = g_split_character.join(_tmps).lower() + g_split_character

    return _next


def traceback_by_stringcode(_code):
    _list = g_tmp_dictionary.get(_code, None)

    if _list is None:
        
        _query = SoundVocabulary.objects.filter(pinyin=_code).first()

        if _query:
            _set = _query.vocabulary.values_list('context', flat=True)
            _list = list(_set)[:3]
            g_tmp_dictionary[_code] = _list
        else:
            _list = [_code]

    return '|'.join(_list)

