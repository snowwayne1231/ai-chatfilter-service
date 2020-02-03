from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
import tensorflow as tf
import tensorflow_datasets as tfds

from .helper import print_spend_time, get_pinyin_path

from service.main import MainService
main_service = MainService()


def predict_by_pinyin(text = '', room = '', silence = False, detail=False):
    
    # _text, _lv, _anchor = message_parser.parse(text)

    results = main_service.think(message=text, user='', room=room, silence=silence, detail=detail)
    prediction = results.get('prediction', 0)
    text = results.get('text', 0)

    return prediction, text

