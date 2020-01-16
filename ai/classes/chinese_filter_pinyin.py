from __future__ import absolute_import, division, print_function, unicode_literals

import os
# from datetime import datetime
from .translator_pinyin import translate_by_string, traceback_by_stringcode
from .chinese_filter_basic import BasicChineseFilter

import tensorflow as tf
from ai.models import DigitalVocabulary



class PinYinFilter(BasicChineseFilter):
    """
    """

    digital_vocabulary_map = {}

    def __init__(self, data = [], load_folder=None):
        
        super().__init__(data=data, load_folder=load_folder)
        vocabularies = DigitalVocabulary.objects.all()
        next_dv_map = {}
        for _ in vocabularies:
            next_dv_map[_.digits] = _.pinyin

        self.digital_vocabulary_map = next_dv_map


    def parse_digit(self, _string):
        return self.digital_vocabulary_map.get(_string, _string)
    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        _words = self.jieba_dict.split_word(_pinyin)
        # print(_pinyin)
        # print(_words)
        # exit(2)
        
        _words = [self.parse_digit(_w) if _w.isdigit() else _w  for _w in _words]
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
    
