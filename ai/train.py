from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
from datetime import datetime

from dataparser.apps import ExcelParser
from dataparser.classes.store import ListPickle
from .classes.pinyin import PinYinFilter



def train_pinyin(excel_file_path = None):

    pinyin_saved_folder = os.path.dirname(os.path.abspath(__file__)) + '/_models/pinyin_model'
    
    tmp_saved_list_path = os.path.dirname(os.path.abspath(__file__)) + '/_pickles/list.pickle'

    _st_time = datetime.now() #

    pk = ListPickle(tmp_saved_list_path)
    
    if excel_file_path is not None:

        ep = ExcelParser(file=excel_file_path)
        basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息'], ['STATUS', '審核結果']]
        result_list = ep.get_row_list(column=basic_model_columns)

        # if is_save_pickle:
        
        pk.save(result_list)

    else:
        
        result_list = pk.get_list()

        if len(result_list) == 0:
            print('Wrong with no file path input.')
            return


    print('The result list length: ', len(result_list))

    
    if os.path.isdir(pinyin_saved_folder):

        piny = PinYinFilter(load_folder=pinyin_saved_folder)

        history = piny.fit_model(epochs=2, train_data=result_list)

    else:

        piny = PinYinFilter(data=result_list)
        # piny.transfrom_column('TEXT')
        piny.build_model()

        history = piny.fit_model(epochs=2, save_folder=pinyin_saved_folder)

        # piny.save(pinyin_saved_folder)

    print('=== history ===')
    print(history)
    _ed_time = datetime.now() #
    _spend_seconds = (_ed_time - _st_time).total_seconds() #
    _left_seconds = int(_spend_seconds % 60)
    _spend_minutes = int(_spend_seconds // 60)
    _left_minutes = int(_spend_minutes % 60)
    _left_hours = int(_spend_minutes // 60)

    print('=== spend time: {:d}:{:d}:{:d}'.format(_left_hours, _left_minutes, _left_seconds))



if __name__ == '__main__':

    handle()