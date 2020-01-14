from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
import tensorflow as tf
import tensorflow_datasets as tfds

from datetime import datetime

# from .classes.chinese_filter_pinyin import PinYinFilter
# from dataparser.apps import MessageParser
from .helper import print_spend_time, get_pinyin_path

# pinyin_saved_folder = get_pinyin_path()
# piny = PinYinFilter(load_folder=pinyin_saved_folder)
# message_parser = MessageParser()

from service.main import MainService
main_service = MainService()


def predict_by_pinyin(text = '', room = '', silence = False):
    
    # _st_time = datetime.now()

    
    # _text, _lv, _anchor = message_parser.parse(text)

    # result = piny.predictText(_text, lv=_lv)

    results = main_service.think(message=text, user='', room=room, silence=silence)
    prediction = results.get('prediction', 0)
    # del results

    # print_spend_time(_st_time)

    return prediction

