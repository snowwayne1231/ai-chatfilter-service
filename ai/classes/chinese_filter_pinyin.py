from __future__ import absolute_import, division, print_function, unicode_literals

import os
from .translator_pinyin import translate_by_string, traceback_by_stringcode
from .chinese_filter_basic import BasicChineseFilter

import tensorflow as tf
from ai.models import DigitalVocabulary, NewVocabulary



class PinYinFilter(BasicChineseFilter):
    """
    """

    digital_vocabulary_map = {}

    def __init__(self, data = [], load_folder=None):
        
        super().__init__(data=data, load_folder=load_folder)
        vocabularies = DigitalVocabulary.objects.all()
        next_dv_map = {}
        for _ in vocabularies:
            _bt_key = '{}_'.format(_.digits)
            next_dv_map[_bt_key] = _.pinyin

        self.digital_vocabulary_map = next_dv_map


    def parse_digit(self, _string):
        return self.digital_vocabulary_map.get(_string, _string)
    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        _words = self.jieba_dict.split_word(_pinyin)
        _words = [self.parse_digit(_w) if _w[:-1].isdigit() else _w  for _w in _words]
        # print(_pinyin)
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


    def add_new_vocabulary(self, _word):
        if self.jieba_dict.is_allowed_word(_word) and self.jieba_dict.is_new_word(_word):
            _new = NewVocabulary(pinyin=_word)
            _new.save()
        return self
    
