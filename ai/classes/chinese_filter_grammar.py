from __future__ import absolute_import, division, print_function, unicode_literals

from ai.models import DigitalVocabulary, NewVocabulary
from .chinese_filter_basic import BasicChineseFilter

import tensorflow as tf
import os, re
import numpy as np




class GrammarFilter(BasicChineseFilter):
    """
    """

    re_is_chinese = re.compile('[\u4e00-\u9fa5]')
    re_is_english = re.compile('[a-zA-Z]')
    re_is_number = re.compile('[0-9]')
    re_is_other = re.compile('[\u0020-\u0085]')

    STATUS_EMPTY = 0
    STATUS_CHINESE = 1
    STATUS_ENGLISH = 2
    STATUS_NUMBER = 3
    STATUS_OTHER = 4
    STATUS_UNKNOW = 5

    status_classsets = 2
    full_words_length = 64


    # def __init__(self, data = [], load_folder=None):
        
    #     super().__init__(data=data, load_folder=load_folder)
    

    # override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _next = []
        for _s in _string:
            if self.re_is_chinese.match(_s):
                _next.append(self.STATUS_CHINESE)
            elif self.re_is_english.match(_s):
                _next.append(self.STATUS_ENGLISH)
            elif self.re_is_number.match(_s):
                _next.append(self.STATUS_NUMBER)
            elif self.re_is_other.match(_s):
                _next.append(self.STATUS_OTHER)
            else:
                _next.append(self.STATUS_UNKNOW)
        # print('transform_str next: ', _next)
        return _next

    
    # override
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.status_classsets

        model = tf.keras.Sequential()
        # model.add(tf.keras.layers.Conv1D(input_shape=(full_words_length,)))
        model.add(tf.keras.layers.Flatten(input_shape=(full_words_length,)))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        model.add(tf.keras.layers.Dense(full_words_length * all_scs, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(all_scs, activation=tf.nn.softmax))

        # model.build()
        model.summary()
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001, amsgrad=True)

        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self


    # override
    def fit_model(self, epochs=1, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)


        batch_train_data = self.get_train_batchs()

        _length_of_data = self.length_x
        
        BATCH_SIZE = 32
        BUFFER_SIZE = _length_of_data + 1
        VALIDATION_SIZE = int(_length_of_data / 8) if _length_of_data > 5000 else int(_length_of_data / 2)

        # print("batch_train_data: ", batch_train_data)
        # for _ in batch_train_data.take(2):
        #     print(_)
        # exit(2)

        if validation_data is None:

            batch_train_data = batch_train_data.shuffle(BUFFER_SIZE, reshuffle_each_iteration=True).repeat(epochs)
            batch_test_data = batch_train_data.take(VALIDATION_SIZE)


        history = None
        batch_train_data = batch_train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))
        batch_test_data = batch_test_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

        # for _ in batch_train_data:                  
        #     print("2 _: ", _)

        # exit(2)

        print('==== batch_train_data ====')
        print('Length of Data :: ', _length_of_data)
        print('BATCH_SIZE :: ', BATCH_SIZE)
        print('BUFFER_SIZE :: ', BUFFER_SIZE)
        print('VALIDATION_SIZE :: ', VALIDATION_SIZE)

        steps = int(_length_of_data / BATCH_SIZE)
        vaildation_steps = int(VALIDATION_SIZE / BATCH_SIZE)

        # print("batch_train_data: ", batch_train_data)
        # for _ in batch_train_data.take(1):
        #     print(_)
        
        # print(list(batch_train_data.take(1).as_numpy_iterator()))
        # exit(2)
        

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
                
                if stop_accuracy:
                    print('Now Accuracy: {:.4f} / Target Accuracy: {:.4f}'.format(acc, stop_accuracy))
                    if acc >= stop_accuracy:
                        break
                
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        
        return history

    

    def get_train_batchs(self):
        
        x, y = self.get_xy_data()
        self.length_x = len(x)

        _full_wl = self.full_words_length

        def gen():
            for idx, texts in enumerate(x):
                if len(texts) == 0:
                    continue

                st = 1 if y[idx] and int(y[idx]) > 0 else 0
                
                yield self.parse_texts(texts), st

        dataset = tf.data.Dataset.from_generator(
            gen,
            ( tf.int32, tf.int32 ),
            ( tf.TensorShape([_full_wl, ]), tf.TensorShape([]) ),
        )

        return dataset


    def parse_texts(self, texts):
        next_txt = []
        _len = len(texts)
        _full_wl = self.full_words_length
        _status_e = self.STATUS_EMPTY
        _left_pad = int((_full_wl - _len) / 2)

        if _left_pad >= 0:
            _right_pad = _full_wl - _left_pad - _len
            next_txt = ([_status_e] * _left_pad) + texts + ([_status_e] * _right_pad)
            
        else:
            next_txt = next_txt[:_full_wl]
        
        return np.array(next_txt)
    

    # override
    def predictText(self, text, lv = 0):
        
        if lv < self.avoid_lv:

            _words = self.transform(text)

            if len(_words) == 0:
                return 0

            _words = self.parse_texts(_words)

            # print('predictText  _words : ', _words, _words.shape)
            
            predicted = self.model.predict(np.array([_words]))
            passible = np.argmax(predicted)

            # print('predicted: ', predicted)
            # print('passible: ', passible)
        
        else:

            passible = 0

        return passible
