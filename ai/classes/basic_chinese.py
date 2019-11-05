from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy
from dataparser.apps import MessageParser

import numpy as np
import tensorflow as tf
import pickle
import json
import os



class BasicChineseFilter():
    """
    """

    columns = ['ROOM', 'ACCOUNT', 'MESSAGE', 'STATUS', 'TEXT', 'LV', 'ANCHOR']
    data = []
    data_processed = []
    model = None
    tokenizer = None
    saved_folder = None
    message_parser = MessageParser()

    full_vocab_size = 32767
    full_words_length = 96
    status_classsets = 8
    appended_columns = ['TEXT', 'LV', 'ANCHOR']
    avoid_lv = 1

    
    def __init__(self, data = [], load_folder=None):
        
        if len(data) > 0:

            if self.check_data_shape(data):

                self.tokenizer = tf.keras.preprocessing.text.Tokenizer()

                self.set_data(data)
            
            else:

                print('Error init with worng length of dataset.')

        elif load_folder:

            self.load(load_folder)


    def check_data_shape(self, data=[]):

        if len(data) == 0:
            data = self.data

        _len_should = len(self.columns) - len(self.appended_columns)
        _isright = len(data[0]) == _len_should

        if _isright == False:
            print('Dataset length wrong of checking function. ')
            print('Dataset length should be ', _len_should)
            print('But ', len(data[0]))

        return _isright
    

    def set_data(self, data):
        if self.check_data_shape(data):

            _data = deepcopy(data)
            _msg_idx = self.columns.index('MESSAGE') if 'MESSAGE' in self.columns else -1
            _text_idx = self.columns.index('TEXT') if 'TEXT' in self.columns else -1
            _lv_idx = self.columns.index('LV') if 'LV' in self.columns else -1
            _anchor_idx = self.columns.index('ANCHOR') if 'ANCHOR' in self.columns else -1
            _appended_length = len(self.columns)

            for d in _data:
                _string = d[_msg_idx]
                text, lv, anchor = self.parse_message(_string)

                # 
                if len(d) == _appended_length:
                    d[_text_idx] = text
                    d[_lv_idx] = lv
                    d[_anchor_idx] = anchor
                else:
                    d.append(text)
                    d.append(lv)
                    d.append(anchor)

            self.data = _data

            self.transfrom_column('TEXT')

    
    def parse_message(self, string):
        return self.message_parser.parse(string)


    def to_tokenization(self, input_str):
        _loc = 0
        if input_str:
        
            if type(input_str) is list:
                input_str = input_str[-1]
            
            _loc = self.get_token_index(input_str)

            if _loc == -1:
                self.tokenizer.fit_on_texts([input_str])
            
            _loc = self.tokenizer.word_index.get(input_str, 0)

        return _loc



    def get_token_index(self, text):
        _text = text.strip().lower()
        _loc = self.tokenizer.word_index.get(_text, -1)
        return _loc



    def transfrom(self, data):
        
        if type(data) is str:

            return data
        elif type(data) is list:
            return [self.transfrom(_) for _ in data]
        
        return None



    def transfrom_column(self, column = 'TEXT'):
        assert len(self.data) > 0

        # _texts = []
        # _data = deepcopy(self.data)

        if type(column) is int:
            column_idx = column
        elif type(column) is str:
            column_idx = self.columns.index(column) if column in self.columns else -1

        assert column_idx >= 0 and column_idx < len(self.columns)

        for d in self.data:
            _text = d[column_idx]
            d[column_idx] = self.transfrom(_text)

            # d[column_idx] = _text_transfromed
            # _texts.append(_text_transfromed)
            
        # self.data_processed = _data

        print('====PinYin transfrom data length: ', len(self.data)) #

        return self



    def save(self, folder = None):
        if folder is not None:
            self.saved_folder = folder
        elif self.saved_folder:
            folder = self.saved_folder
        else:
            print('Error Save, because folder is not specify')
            return None
        
        if not os.path.isdir(folder):
            os.mkdir(folder)
        
        self.save_model(folder + '/model.h5')
        self.save_tokenizer(folder + '/tokenizer.pickle')
        self.save_columns(folder + '/columns.pickle')
        print('Successful saved.')



    def load(self, folder):
        self.saved_folder = folder
        self.load_model(folder + '/model.h5')
        self.load_tokenizer(folder + '/tokenizer.pickle')
        self.load_columns(folder + '/columns.pickle')
    

    
    def save_tokenizer(self, path):
        with open(path, 'wb+') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)



    def load_tokenizer(self, path):
        with open(path, 'rb') as handle:
            self.tokenizer = pickle.load(handle)



    def save_model(self, path):
        return self.model.save(path)
    


    def load_model(self, path):
        _model = tf.keras.models.load_model(path)
        self.model = _model
        return _model



    def save_columns(self, path):
        with open(path, 'wb+') as handle:
            pickle.dump(self.columns, handle, protocol=pickle.HIGHEST_PROTOCOL)



    def load_columns(self, path):
        with open(path, 'rb') as handle:
            self.columns = pickle.load(handle)
    
    

    def build_model(self):
        full_words_length = self.full_words_length

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, full_words_length))
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length, return_sequences=True)))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64)))
        # model.add(tf.keras.layers.GlobalAveragePooling1D())
        # model.add(tf.keras.layers.Flatten())
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.sigmoid))
        model.add(tf.keras.layers.Dense(self.status_classsets, activation=tf.nn.softmax))

        model.summary()
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self



    def fit_model(self, epochs=5, batch_size=512, verbose=1, train_data=None, save_folder=None, validation_data=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)
        
        train_x, train_y = self.get_xy_data()

        np_train_x = np.array(train_x)
        np_train_y = np.array(train_y)

        if validation_data is None:
            total_length = len(train_x)
            pp = int(total_length / 10)
            p2 = pp * 2

            validation_x = np.array(np_train_x[pp:p2])
            validation_y = np.array(np_train_y[pp:p2])
        else:
            validation_x = np.array(validation_data.x)
            validation_y = np.array(validation_data.y)

        print('====fit model train_x length: ', len(train_x))
        print('=======fit model train_x[0] ', train_x[0])
        print('====fit model train_y length: ', len(train_y))
        print('=======fit model train_y[0] ', train_y[0])


        history = None

        try:
            while True:
                history = self.model.fit(
                    np_train_x,
                    np_train_y,
                    epochs=epochs,
                    # batch_size=batch_size,
                    verbose=verbose,
                    validation_data=(validation_x, validation_y),
                )
                self.save()
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        
        return history



    def truncate_pad_words(self, words):
        full_words_length = self.full_words_length
        words_length = len(words)
        if words_length >= full_words_length:
            return words[:full_words_length]
        else:
            return words + ((full_words_length - words_length) * [0])



    def get_xy_data(self):
        x_idx = self.columns.index('TEXT') if 'TEXT' in self.columns else -1
        vip_lv_idx = self.columns.index('LV') if 'LV' in self.columns else -1
        y_idx = self.columns.index('STATUS') if 'STATUS' in self.columns else -1
        new_x = []
        new_y = []

        for _d in self.data:
            if _d[x_idx] and _d[vip_lv_idx] < self.avoid_lv:

                _paded_text = self.truncate_pad_words(_d[x_idx])
                new_x.append(_paded_text)
                new_y.append(self.parse_to_array_num_class(_d[y_idx]))
        
        return new_x, new_y



    def drop_data_json(self, file = ''):
        if file == '':
            return self

        with open(file, 'w+', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False)
        
        return self



    def predictText(self, text):
        _text, _lv, _anchor = self.parse_message(text)
        if _lv < self.avoid_lv:

            _text = self.transfrom(_text)
            _text = self.truncate_pad_words(_text)

            test_data = np.array([_text])
            
            predicted = self.model.predict(test_data)[0]
            passible = np.argmax(predicted)

            # print('predicted: ', predicted)
        
        else:

            passible = 0

        # print('predictText _text: ', _text)
        # print('Text: ', text)
        # print('Prosessed text: ', _text)
        # print('The most likely possible status: ', passible)
        return passible



    def parse_to_array_num_class(self, i):
        return tf.keras.utils.to_categorical(int(i), num_classes=self.status_classsets)




class onPredictionCallback(tf.keras.callbacks.Callback):

    def on_predict_end(self, logs=None):
        print('predict end: ')
        print(logs)
        pass
        return super().on_predict_end(logs=logs)

    def on_test_end(self, logs=None):
        print('on_test_end: ')
        print(logs)
        return super().on_test_end(logs=logs)