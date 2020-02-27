from __future__ import absolute_import, division, print_function, unicode_literals

import os
from .chinese_filter_basic import BasicChineseFilter

import tensorflow as tf
from ai.models import DigitalVocabulary, NewVocabulary



class GrammarFilter(BasicChineseFilter):
    """
    """


    def __init__(self, data = [], load_folder=None):
        
        super().__init__(data=data, load_folder=load_folder)

    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        _words = self.jieba_dict.split_word(_pinyin)
        _words = [self.parse_digit(_w) if _w[:-1].isdigit() else _w  for _w in _words]
        # print(_pinyin)
        # print(_words)
        return _words

    
    # overrie
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.status_classsets

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, all_scs))
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs, return_sequences=True)))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(all_scs, activation=tf.nn.softmax))

        model.summary()
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.002, amsgrad=True)

        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self


    
