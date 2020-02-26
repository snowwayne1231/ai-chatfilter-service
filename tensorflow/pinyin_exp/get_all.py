from django.core.management.base import BaseCommand
from pypinyin import pinyin, Style
# from ai.classes.translator_pinyin import translate_by_string
import os, re
import jieba, json

regex_chinese = re.compile('[\u4e00-\u9fa5]+')
regex_english = re.compile('[a-zA-Z0-9]+')

def doing():
    _chinese_start = int(0x4e00)
    _chinese_end = int(0x9fa5)
    _all_words = []
    _all_pinyin = []
    _set_pinyin = {}

    for __i in range(_chinese_end - _chinese_start):
        __str = chr(__i + _chinese_start)
        __pinyin = pinyin(__str, strict=True, style=Style.TONE3, heteronym=True)
        # __pinyin = pinyin(__str, strict=True, style=Style.NORMAL, heteronym=True)
        for _p in __pinyin:
            for __p in _p:
                if regex_english.match(__p):
                    _origin = _set_pinyin.get(__p, '')
                    _origin += __str
                    _set_pinyin[__p] = _origin
                    break

        _all_words.append(__str)
        _all_pinyin.append(__pinyin)

    _sorted_list = sorted(_set_pinyin)
    res_list = []
    for _ in _sorted_list:
        _loc = _set_pinyin.get(_)
        # _str = '{}_ {} {}'.format(_, 1, _loc)
        _str = '{}_ {}'.format(_, 1)
        res_list.append(_str)
    
    # print(_set_pinyin)
    
    # print(_sorted_list)

    # print('length of all pinyin: ', len(_sorted_list))

    file_object = open(os.path.dirname(__file__)+'/__dict__.json', 'w', encoding='utf8')
    output_str = '\r'.join(res_list)
    file_object.write(output_str)
    file_object.close()
    
    # json_string = json.dumps(_set_pinyin)
    # json.dump(res_list, file_object, indent=2, ensure_ascii=False)
    




if __name__ == '__main__':
    doing()

        