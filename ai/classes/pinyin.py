from __future__ import absolute_import, division, print_function, unicode_literals

import os
# from datetime import datetime
from pypinyin import pinyin, Style
# import tensorflow as tf

# import random

# from _classes.parsers import ExcelParser
from .basic_chinese import BasicChineseFilter
from dataparser.classes.store import ListPickle



class PinYinFilter(BasicChineseFilter):
    """
    """

    strict = False

    def __init__(self, data = [], strict=False, load_folder=None):
        
        self.strict = strict
        
        super().__init__(data=data, load_folder=load_folder)


    def transfrom(self, data):
        
        if type(data) is str:
            
            _next = pinyin(data, strict=self.strict, style=Style.NORMAL, heteronym=True)

            if type(_next) is list:
                _next = list(map(lambda a: a[-1], _next))

            return _next
            
        elif type(data) is list:
            return [self.transfrom(_) for _ in data]
        
        return None