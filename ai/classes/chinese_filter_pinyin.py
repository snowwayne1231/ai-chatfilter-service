from __future__ import absolute_import, division, print_function, unicode_literals

import os
# from datetime import datetime
from .translator_pinyin import translate_by_string, traceback_by_stringcode
import tensorflow as tf


from .chinese_filter_basic import BasicChineseFilter



class PinYinFilter(BasicChineseFilter):
    """
    """
    def __init__(self, data = [], load_folder=None):
        
        super().__init__(data=data, load_folder=load_folder)

    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        _words = self.jieba_dict.split_word(_pinyin)
        # print(_pinyin)
        # print(_words)
        # exit(2)
        
        # _words = _pinyin.split('|')
        _words = [_w for _w in _words if not _w.isdigit()]
        # print(_words)
        return _words


    def transform_back_str(self, _encoded):
        _type = type(_encoded)
        if _type is str:
            return traceback_by_stringcode(_encoded)
        elif _type is list:
            return [self.transform_back_str(_) for _ in _encoded]
        else:
            return _encoded
    
