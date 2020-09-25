import re

classification_map = {
    'reserve': 0,
    'general_symbol': 1,

}

classifications = [
    (u'\u0000', u'\u0019'),
    (u'\u0020', u'\u0082'), # general english, digits and symbol


    (u'\u3001', u'\u3002'), # dot symbol

    (u'\u4e00', u'\u9fa5'), # chinese

    (u'\uff01', u'\uff65'), # full type of english, digits and symbol

    (u'\U0001f600', u'\U0001f64f'), # faces
    (u'\U0001f910', u'\U0001f9ff'), # faces
]

regex_chinese = re.compile('[\u4e00-\u9fa5]+')
regex_korea = re.compile('[\uac00-\ud7a3]+')
regex_full_char = re.compile('[\uff01-\uff65]+')

allowed_character_regexies = [
    (u'\u0020', u'\u0082'), # general english, digits and symbol
    # (u'\u23e9', u'\u23f9'), # symbol
    # (u'\u26bd', u'\u270d'), # symbol
    (u'\u3001', u'\u3002'), # dot symbol
    # (u'\u3105', u'\u3129'), # zuyin
    (u'\u4e00', u'\u9fa5'), # chinese
    # (u'\u3041', u'\u30ff'), # japanese
    # (u'\u1100', u'\u11f9'), # korea yin
    # (u'\u3131', u'\u318e'), # korea yin 2
    # (u'\uac00', u'\ud7a3'), # korea
    # (u'\uff01', u'\uff65'), # full type of english, digits and symbol
    # (u'\U0001f600', u'\U0001f64f'), # faces
    # (u'\U0001f910', u'\U0001f9ff'), # faces
]


languages = [
    {'type': 'number', 'range': [(u'\u0030', u'\u0039')], 'regex': re.compile('.*[\u0030-\u0039]+')},
    {'type': 'english', 'range': [(u'\u0041', u'\u007a')], 'regex': re.compile('.*[\u0041-\u007a]+')},
    {'type': 'chinese', 'range': [(u'\u4e00', u'\u9fa5')], 'regex': re.compile('.*[\u4e00-\u9fa5]+')},
]


def is_allowed_character(uchar):
    for _ in allowed_character_regexies:
        _st = _[0]
        _ed = _[1]
        if _st <= uchar <= _ed:
            return True
    return False


def find_not_allowed_chat(text):
    next_char = ''

    for u in text:
        if not is_allowed_character(u):
            next_char += u

    return next_char


def is_mix_multiple_language(text):
    _num_lan = 0
    for _lan in languages:
        _reg = _lan['regex']
        if _reg.match(text):
            _num_lan += 1
        
    return _num_lan >= 2


def parse_to_half_char(text):
    # full char to half
    _minus = 0xfee0
    next_char = ''

    for _ in text:
        if regex_full_char.match(_):
            _code = ord(_)
            _char = chr(_code - _minus)
        else:
            _char = _
        
        next_char += _char

    return next_char