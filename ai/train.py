from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
import tensorflow as tf
import tensorflow_datasets as tfds

from datetime import datetime

from dataparser.apps import ExcelParser, MessageParser
from dataparser.classes.store import ListPickle
from .classes.chinese_filter_pinyin import PinYinFilter
from .classes.chinese_filter_grammar import GrammarFilter
from .helper import print_spend_time, get_pinyin_path, get_grammar_path



def train_pinyin(excel_file_path = None, is_append = False, final_accuracy = None, max_spend_time=0):

    pinyin_saved_folder = get_pinyin_path()
    
    # tmp_saved_list_path = os.path.dirname(os.path.abspath(__file__)) + '/_pickles/list.pickle'

    _st_time = datetime.now() #

    # pk = ListPickle(tmp_saved_list_path)
    
    if excel_file_path is not None:

        ep = ExcelParser(file=excel_file_path)
        basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息', '禁言内容', '发言内容'], ['STATUS', '審核結果', '状态']]
        result_list = ep.get_row_list(column=basic_model_columns)

        # print('result_list[0]', result_list[0])

        # if is_save_pickle:

        message_parser = MessageParser()
        for res in result_list:
            msg = res[2]
            text, lv, anchor = message_parser.parse(msg)

            res.append(text)
            res.append(lv)
            res.append(anchor)
    else:

        result_list = []
    


    # if is_append or len(result_list) == 0:
    #     result_list = result_list + pk.get_list()

    if len(result_list) == 0:
        print('Wrong with no file path input.')
        return
     
    # pk.save(result_list)

    print('The result list length: ', len(result_list))

    #for test..
    # result_list = result_list[27800:28000]
    # print('result_list[:5] = ', result_list[:5])

    
    if os.path.isdir(pinyin_saved_folder):

        piny = PinYinFilter(load_folder=pinyin_saved_folder)

        history = piny.fit_model(train_data=result_list, stop_accuracy=final_accuracy, stop_hours=max_spend_time)

    else:

        piny = PinYinFilter(data=result_list)
        # piny.transfrom_column('TEXT')
        piny.build_model()

        history = piny.fit_model(save_folder=pinyin_saved_folder, stop_accuracy=final_accuracy, stop_hours=max_spend_time)

        # piny.save(pinyin_saved_folder)

    print('=== history ===')
    print(history)
    print_spend_time(_st_time)




def train_grammar(excel_file_path = None, is_append = False, final_accuracy = None, max_spend_time=0):

    _saved_folder = get_grammar_path()

    _st_time = datetime.now() #
    
    if excel_file_path:

        ep = ExcelParser(file=excel_file_path)
        basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息', '禁言内容', '发言内容'], ['STATUS', '審核結果', '状态']]
        result_list = ep.get_row_list(column=basic_model_columns)

        # print('result_list[0]', result_list[0])

        # if is_save_pickle:

        message_parser = MessageParser()
        for res in result_list:
            msg = res[2]
            text, lv, anchor = message_parser.parse(msg)

            res.append(text)
            res.append(lv)
            res.append(anchor)
    

    print('The result list length: ', len(result_list))

    
    if os.path.isdir(_saved_folder):

        model = GrammarFilter(load_folder=_saved_folder)

        history = model.fit_model(train_data=result_list, stop_accuracy=final_accuracy, stop_hours=max_spend_time)

    else:

        model = GrammarFilter(data=result_list)
        model.build_model()

        history = model.fit_model(save_folder=_saved_folder, stop_accuracy=final_accuracy, stop_hours=max_spend_time)


    print('=== history ===')
    print(history)
    print_spend_time(_st_time)