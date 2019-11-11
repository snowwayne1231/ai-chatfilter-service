from __future__ import absolute_import, division, print_function, unicode_literals
from datetime import datetime
import os

def print_spend_time(_st_time):
    _ed_time = datetime.now() #
    _spend_seconds = (_ed_time - _st_time).total_seconds() #
    _left_seconds = int(_spend_seconds % 60)
    _spend_minutes = int(_spend_seconds // 60)
    _left_minutes = int(_spend_minutes % 60)
    _left_hours = int(_spend_minutes // 60)
    print('==== spend time: {:d} h: {:d} m: {:d} s'.format(_left_hours, _left_minutes, _left_seconds))
    return _spend_seconds


def get_pinyin_path():
    return os.path.dirname(os.path.abspath(__file__)) + '/_models/pinyin_model'