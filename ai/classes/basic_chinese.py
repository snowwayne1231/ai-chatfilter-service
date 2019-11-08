from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy
from dataparser.apps import MessageParser

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
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
    tokenizer_vocabulary = set()
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

                # self.tokenizer = tf.keras.preprocessing.text.Tokenizer()
                self.tokenizer = tfds.features.text.Tokenizer()

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

        return self



    def save(self, folder = None):
        if folder is not None:
            self.saved_folder = folder
        elif self.saved_folder:
            folder = self.saved_folder
        else:
            print('Error Save, because folder is not specify')
            return None
        
        if not os.path.isdir(folder) or not os.path.exists(folder):
            os.makedirs(folder)
        
        self.save_model(folder + '/model.h5')
        self.save_tokenizer_vocabulary(folder + '/tokenizer_vocabulary.pickle')
        self.save_columns(folder + '/columns.pickle')
        print('Successful saved.')



    def load(self, folder):
        self.saved_folder = folder
        self.load_model(folder + '/model.h5')
        self.load_tokenizer_vocabulary(folder + '/tokenizer_vocabulary.pickle')
        self.load_columns(folder + '/columns.pickle')
    

    
    def save_tokenizer_vocabulary(self, path):
        with open(path, 'wb+') as handle:
            pickle.dump(self.tokenizer_vocabulary, handle, protocol=pickle.HIGHEST_PROTOCOL)



    def load_tokenizer_vocabulary(self, path):
        with open(path, 'rb') as handle:
            self.tokenizer_vocabulary = pickle.load(handle)



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
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length, return_sequences=True)))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64)))
        # model.add(tf.keras.layers.GlobalAveragePooling1D())
        # model.add(tf.keras.layers.Flatten())
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.sigmoid))
        model.add(tf.keras.layers.Dense(self.status_classsets, activation=tf.nn.softmax))

        model.summary()
        
        model.compile(
            optimizer='adam',
            # loss='categorical_crossentropy',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        self.model = model

        return self



    def fit_model(self, epochs=5, batch_size=512, verbose=1, train_data=None, save_folder=None, validation_data=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)


        batch_train_data = self.get_train_batchs()

        # np_train_x = np.array(train_x)
        # np_train_y = np.array(train_y)

        BUFFER_SIZE = 50000
        BATCH_SIZE = self.full_words_length

        if validation_data is None:

            batch_test_data = batch_train_data.take(1000)
            batch_train_data = batch_train_data.skip(1000).shuffle(BUFFER_SIZE, reshuffle_each_iteration=False)

        else:

            batch_test_data = self.bathchs_labeler(validation_data.x, validation_data.y)

        history = None
        batch_train_data = batch_train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))
        batch_test_data = batch_test_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

        print('==== batch_train_data ====')

        for x, y in batch_train_data.take(1):
            print('= batch_train_data =')
            print(x)
            print(y)

        # return False

        try:
            while True:
                history = self.model.fit(
                    batch_train_data,
                    epochs=epochs,
                    verbose=verbose,
                    validation_data=batch_test_data,
                )
                self.save()
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        
        return history



    def tokenize_data(self, datalist):
        tokenizer_vocabulary = self.tokenizer_vocabulary
        tokenizer = tfds.features.text.Tokenizer()
        for texts in datalist:
            for txt in texts:
                tokens = tokenizer.tokenize(txt)
                tokenizer_vocabulary.update(tokens)
        
        vocab_size = len(tokenizer_vocabulary)
        print('tokenizer_vocabulary vocab_size = ', vocab_size)
        # print(vocabulary_set)
        self.tokenizer_vocabulary = tokenizer_vocabulary

        return tokenizer_vocabulary



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

                # _paded_text = self.truncate_pad_words(_d[x_idx])
                new_x.append(_d[x_idx])

                # _state_class = self.parse_to_array_num_class(_d[y_idx])
                new_y.append(_d[y_idx])
        
        return new_x, new_y



    def get_train_batchs(self):

        x, y = self.get_xy_data()

        print('======== get_train_batchs =========')
        tokenize_set = self.tokenize_data(x)

        labeled_dataset = self.bathchs_labeler(x, y)

        return labeled_dataset



    def bathchs_labeler(self, x, y):
        assert len(x) == len(y)
        encoder = tfds.features.text.TokenTextEncoder(self.tokenizer_vocabulary)

        def encode(text):
            encoded_list = encoder.encode(text)
            if len(encoded_list) > 0:
                return encoded_list[0]
            else:
                return 0

        def gen():
            for idx, texts in enumerate(x):
                next_texts = []
                for text in texts:
                    encoded_text = encode(text)
                    next_texts.append(encoded_text)
                
                yield next_texts, y[idx]
        
        dataset = tf.data.Dataset.from_generator(gen, (tf.int64, tf.int64), (tf.TensorShape([None]), tf.TensorShape([])))

        # print(dataset.take(1))
        # for __ in dataset.take(10):
        #     print(__)

        return dataset



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
            # _text = self.truncate_pad_words(_text)

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



