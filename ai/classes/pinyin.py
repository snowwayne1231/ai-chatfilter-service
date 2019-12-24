from __future__ import absolute_import, division, print_function, unicode_literals

import os
# from datetime import datetime
from pypinyin import pinyin, Style
import tensorflow as tf

# import random

# from _classes.parsers import ExcelParser
from .basic_chinese import BasicChineseFilter
# from dataparser.classes.store import ListPickle



class PinYinFilter(BasicChineseFilter):
    """
    """

    strict = False

    def __init__(self, data = [], strict=False, load_folder=None):
        
        self.strict = strict
        
        super().__init__(data=data, load_folder=load_folder)

    
    #override
    def transfrom(self, data):
        
        if type(data) is str:
            
            _words = pinyin(data, strict=self.strict, style=Style.NORMAL, heteronym=True)

            # if type(_next) is list:
            #     _next = list(map(lambda a: a[-1], _next))
            _words = [_w[0] for _w in _words]

            _next = '|'.join(_words)

            # print('pinyin _next: ', _next)

            return _next
            
        elif type(data) is list:
            return [self.transfrom(_) for _ in data]
        
        return None
    

    #override
    def build_model(self):
        full_words_length = self.full_words_length

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, full_words_length))
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(self.status_classsets, activation=tf.nn.softmax))

        model.summary()
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.005, amsgrad=True)

        model.compile(
            optimizer=optimizer,
            # loss='categorical_crossentropy',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self


    #override
    def fit_model(self, epochs=1, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)


        batch_train_data = self.get_train_batchs()

        _length_of_data = self.length_x

        BUFFER_SIZE = 50000
        BATCH_SIZE = self.full_words_length
        VALIDATION_SIZE = 1000 if _length_of_data > 2000 else int(_length_of_data / 2)

        

        if validation_data is None:

            batch_test_data = batch_train_data.take(VALIDATION_SIZE)
            batch_train_data = batch_train_data.skip(VALIDATION_SIZE).shuffle(BUFFER_SIZE, reshuffle_each_iteration=False)
            _length_of_data -= VALIDATION_SIZE

        else:

            batch_test_data = self.bathchs_labeler(validation_data.x, validation_data.y)

        history = None
        batch_train_data = batch_train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[])).repeat(epochs)
        batch_test_data = batch_test_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

        print('==== batch_train_data ====')
        print('Length of Data :: ', _length_of_data)
        print('BUFFER_SIZE :: ', BUFFER_SIZE)
        print('BATCH_SIZE :: ', BATCH_SIZE)
        print('VALIDATION_SIZE :: ', VALIDATION_SIZE)
        

        # for x, y in batch_train_data.take(1):
        #     print('= batch_train_data =')
        #     print(x)
        #     print(y)

        # return False

        steps = int(_length_of_data / BATCH_SIZE)
        vaildation_steps = int(VALIDATION_SIZE / BATCH_SIZE)

        try:
            while True:
                history = self.model.fit(
                    batch_train_data,
                    epochs=epochs,
                    verbose=verbose,
                    validation_data=batch_test_data,
                    steps_per_epoch=steps,
                    validation_steps=vaildation_steps,
                )
                self.save()

                acc = history.history.get('accuracy')[-1]
                print('Now Accuracy: ', acc)
                print('Target Accuracy: ', stop_accuracy)
                if stop_accuracy and acc >= stop_accuracy:
                    break
                
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        
        return history
