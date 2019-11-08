from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
from datetime import datetime

from dataparser.apps import ExcelParser
from dataparser.classes.store import ListPickle
from .classes.pinyin import PinYinFilter

import tensorflow as tf
import tensorflow_datasets as tfds

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




def load_data():
    (train_data, test_data), info = tfds.load(
        # Use the version pre-encoded with an ~8k vocabulary.
        'imdb_reviews/subwords8k', 
        # Return the train/test datasets as a tuple.
        split = (tfds.Split.TRAIN, tfds.Split.TEST),
        # Return (example, label) pairs from the dataset (instead of a dictionary).
        as_supervised=True,
        # Also return the `info` structure. 
        with_info=True)

    print('== load_data ==')
    print(train_data)
    print(test_data)
    print('===================')
    # print(info)

    for train_example, train_label in train_data.take(1):
        print(train_example)
        print(train_label)

    BUFFER_SIZE = 1000

    print('========== train_data =============')
    print(train_data)

    print('====== shffled ======')
    shuffled = train_data.shuffle(BUFFER_SIZE)
    print(shuffled)

    print('====== train_batches ========')

    train_batches = (shuffled.padded_batch(32, train_data.output_shapes))

    print(train_batches)

    print('=====================')
    print('tensorflow version: ', tf.__version__)

    lists = [[1,2,3,4], [2,3,4,5]]

    def labeler(example, index):
        return example, tf.cast(index, tf.int32)  

    labeled_data_sets = []

    lines_dataset = tf.data.Dataset.from_tensor_slices(lists)
    labeled_dataset = lines_dataset.enumerate().map(lambda i,ex: labeler(ex, i))
    # labeled_data_sets.append(labeled_dataset)

    qq = labeled_dataset
    

    print(qq)
    for a,b in qq.take(1):
        print(a)
        print(b)
        
    qqs = qq.shuffle(1)
    print(qqs)