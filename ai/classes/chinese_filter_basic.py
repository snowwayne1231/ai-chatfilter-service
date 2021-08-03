from __future__ import absolute_import, division, print_function, unicode_literals
import ast

# from copy import deepcopy

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
import os
from ai.classes.basic_filter import BasicFilter



class BasicChineseFilter(BasicFilter):
    """
    """

    # columns = ['ROOM', 'ACCOUNT', 'MESSAGE', 'STATUS', 'TEXT', 'LV', 'ANCHOR']
    # avoid_lv = 3

    # override
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.num_status_classs

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, full_words_length, mask_zero=True))
        # model.add(tf.keras.layers.Flatten())
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        # model.add(tf.keras.layers.GlobalAveragePooling1D())
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs, return_sequences=True)))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(all_scs, activation=tf.nn.softmax))

        model.summary()
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001, amsgrad=True)

        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self
