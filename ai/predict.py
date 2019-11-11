from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt
import tensorflow as tf
import tensorflow_datasets as tfds

from datetime import datetime

from .classes.pinyin import PinYinFilter
from .helper import print_spend_time, get_pinyin_path


def predict_by_pinyin(text = ''):
    
    pinyin_saved_folder = get_pinyin_path()

    _st_time = datetime.now() #

    
    if os.path.isdir(pinyin_saved_folder):

        piny = PinYinFilter(load_folder=pinyin_saved_folder)

        result = piny.predictText(text)

    else:

        print('Wrong with no pinyin models exist.')
        return False
        # piny.save(pinyin_saved_folder)

    print_spend_time(_st_time)

    




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