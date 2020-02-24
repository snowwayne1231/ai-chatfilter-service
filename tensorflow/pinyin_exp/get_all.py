from django.core.management.base import BaseCommand
from pypinyin import pinyin, Style
# from ai.classes.translator_pinyin import translate_by_string
import os

# regex_chinese = re.compile('[\u4e00-\u9fa5]+')

def doing():
    _chinese_start = int(0x4e00)
    _chinese_end = int(0x9fa5)
    _all_words = []
    _all_pinyin = []
    __i = _chinese_start

    for __i in range(_chinese_end - _chinese_start):
        __str = chr(__i + _chinese_start)
        __i += 1
        __pinyin = pinyin(__str, strict=True, style=Style.NORMAL, heteronym=True)
        _all_words.append(__str)
        _all_pinyin.append(__pinyin)

   
    
    print(_all_words[:10])
    print(_all_pinyin[:10])
    




if __name__ == '__main__':
    doing()

        