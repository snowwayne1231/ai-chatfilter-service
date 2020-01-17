from __future__ import absolute_import, division, print_function, unicode_literals

# from copy import deepcopy
from dataparser.apps import JieBaDictionary

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
import pickle
import json
import os
import sys



class BasicChineseFilter():
    """
    """

    columns = ['ROOM', 'ACCOUNT', 'MESSAGE', 'STATUS', 'TEXT', 'LV', 'ANCHOR']
    appended_columns = ['TRANSFORMED_WORD']
    data = []
    model = None
    tokenizer_vocabulary = set()
    encoder = None
    saved_folder = None
    jieba_dict = None

    full_vocab_size = 32767
    full_words_length = 64
    status_classsets = 8
    avoid_lv = 6
    length_x = 0

    
    def __init__(self, data = [], load_folder=None):

        self.jieba_dict = JieBaDictionary()
        
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

        _len_should = len(self.columns)
        _isright = len(data[0]) == _len_should

        if _isright == False:
            print('Dataset length wrong of checking function. ')
            print('Dataset length should be ', _len_should)
            print('But ', len(data[0]))

        return _isright
    

    def set_data(self, data):
        if self.check_data_shape(data):

            self.data = data

            # self.split_word('TEXT')
            self.transform_column('TEXT')

        else:
            
            print('Set data failed.')

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
        
        print('Successful saved. ')



    def load(self, folder):
        self.saved_folder = folder
        self.load_model(folder + '/model.h5')
        self.load_tokenizer_vocabulary(folder + '/tokenizer_vocabulary.pickle')
        
        print('Successful load model. ', folder)
    

    
    def save_tokenizer_vocabulary(self, path):
        with open(path, 'wb+') as handle:
            pickle.dump(self.tokenizer_vocabulary, handle, protocol=pickle.HIGHEST_PROTOCOL)



    def load_tokenizer_vocabulary(self, path):
        with open(path, 'rb') as handle:
            self.tokenizer_vocabulary = pickle.load(handle)
            self.encoder = tfds.features.text.TokenTextEncoder(self.tokenizer_vocabulary)



    def save_model(self, path):
        return self.model.save(path)
    


    def load_model(self, path):
        _model = tf.keras.models.load_model(path)
        self.model = _model
        return _model



    def transform(self, data):
        
        if type(data) is str:
            return self.transform_str(data)
        elif type(data) is list:
            return [self.transform(_) for _ in data]
        
        return None



    def transform_column(self, column = 'TEXT'):
        assert len(self.data) > 0

        _full_columns = self.columns + self.appended_columns

        if type(column) is int:
            column_idx = column
        elif type(column) is str:
            column_idx = _full_columns.index(column) if column in _full_columns else -1

        assert column_idx >= 0

        _transformed_idx = _full_columns.index('TRANSFORMED_WORD')
        _length_of_columns = len(_full_columns)

        for d in self.data:
            _text = d[column_idx]
            _transformed_words = self.transform(_text)

            if len(d) == _length_of_columns:
                d[_transformed_idx] = _transformed_words
            else:
                d.append(_transformed_words)

        return self


    # should be override
    def transform_str(self, _string):
        return _string

    # should be override
    def transform_back_str(self, _encoded):
        return _encoded



    def build_model(self):
        full_words_length = self.full_words_length

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, full_words_length))
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length)))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(full_words_length, return_sequences=True)))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64)))
        # model.add(tf.keras.layers.GlobalAveragePooling1D())
        # model.add(tf.keras.layers.Flatten())
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.sigmoid))
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



    def fit_model(self, epochs=1, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)


        batch_train_data = self.get_train_batchs()

        _length_of_data = self.length_x

        BUFFER_SIZE = 50000
        BATCH_SIZE = self.full_words_length
        VALIDATION_SIZE = int(_length_of_data / 8) if _length_of_data > 5000 else int(_length_of_data / 2)

        # exit(2)

        if validation_data is None:

            batch_train_data = batch_train_data.shuffle(BUFFER_SIZE, reshuffle_each_iteration=False)
            batch_test_data = batch_train_data.take(VALIDATION_SIZE)
            
            # batch_train_data = batch_train_data.skip(VALIDATION_SIZE)
            # _length_of_data -= VALIDATION_SIZE

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
                
                if stop_accuracy:
                    print('Now Accuracy: {:.4f} / Target Accuracy: {:.4f}'.format(acc, stop_accuracy))
                    if acc >= stop_accuracy:
                        break
                
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        
        return history



    def tokenize_data(self, datalist):
        tokenizer_vocabulary = self.tokenizer_vocabulary
        tokenizer = tfds.features.text.Tokenizer()
        for words in datalist:
            
            for word in words:
                tokens = tokenizer.tokenize(word)
                tokenizer_vocabulary.update(tokens)
            
        vocab_size = len(tokenizer_vocabulary)
        print('tokenizer_vocabulary vocab_size = ', vocab_size)
        # print(vocabulary_set)
        self.tokenizer_vocabulary = tokenizer_vocabulary

        return tokenizer_vocabulary



    def get_xy_data(self):
        _full_columns = self.columns + self.appended_columns
        # x_idx = self.columns.index('TEXT') if 'TEXT' in self.columns else -1
        x_idx = _full_columns.index('TRANSFORMED_WORD') if 'TRANSFORMED_WORD' in _full_columns else -1
        vip_lv_idx = _full_columns.index('LV') if 'LV' in _full_columns else -1
        y_idx = _full_columns.index('STATUS') if 'STATUS' in _full_columns else -1
        new_x = []
        new_y = []

        for _d in self.data:
            if _d[x_idx] and _d[vip_lv_idx] < self.avoid_lv:

                new_x.append(_d[x_idx])
                new_y.append(_d[y_idx])
        
        return new_x, new_y



    def get_train_batchs(self):

        x, y = self.get_xy_data()
        length_x = len(x)
        assert length_x > 0
        self.length_x = length_x

        print('======== get_train_batchs =========')
        print('total x data = ', length_x)

        tokenize_set = self.tokenize_data(x)

        labeled_dataset = self.bathchs_labeler(x, y)

        return labeled_dataset



    def bathchs_labeler(self, x, y):
        assert len(x) == len(y)
        self.encoder = encoder = tfds.features.text.TokenTextEncoder(self.tokenizer_vocabulary)

        def encode(text):
            encoded_list = encoder.encode(text)
            if len(encoded_list) > 0:
                return encoded_list[0]
            else:
                return 0

        def gen():
            for idx, texts in enumerate(x):
                next_texts = []
                st = y[idx] if y[idx] else 0

                for text in texts:
                    encoded_text = encode(text)
                    if encoded_text:
                        next_texts.append(encoded_text)
                    # else:
                    #     print('text: ', text)
                    
                yield next_texts, st
        
        dataset = tf.data.Dataset.from_generator(
            gen,
            ( tf.int64, tf.int64 ),
            ( tf.TensorShape([None]), tf.TensorShape([]) ),
        )

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



    def predictText(self, text, lv = 0):
        # _text, _lv, _anchor = self.parse_message(text)
        
        if lv < self.avoid_lv:

            _words = self.transform(text)

            # print('predictText _words: ', _words)

            _result_text = self.get_encode_word(_words)

            # print('encoded _text : ', _text)

            if len(_result_text) == 0:
                return 0

            
            predicted = self.model.predict([_result_text])[0]
            passible = np.argmax(predicted)

            # print('predicted: ', predicted)
            # print('passible: ', passible)
        
        else:

            passible = 0

        # print('The most likely possible status: ', passible)
        return passible


    def get_reason(self, text, prediction):
        reason = ''
        _words = self.transform(text)

        # print('get_reason _words: ', _words)

        _result_text = self.get_encode_word(_words)

        # print('get_reason _result_text: ', _result_text)

        _res = self.model.predict(_result_text)
        _i = 0
        for _ in _res:
            _max = np.argmax(_)
            if _max == prediction:
                vocabulary = _words[_i]
                # print('vocabulary: ', vocabulary)
                reason = self.transform_back_str(vocabulary)
                break
            _i += 1

        # print('get_reason _res: ', _res)

        # print('get_reason: ', reason)
        
        return reason


    def get_encode_word(self, _words):
        _result_text = []
        for _ in _words:
            _loc = self.encoder.encode(_)
            if len(_loc) > 0:
                _result_text.append(_loc[0])

        return _result_text


    
    def get_details(self, text):
        words = self.transform(text)
        result_text = self.get_encode_word(words)

        predicted = self.model.predict([result_text])[0]
        return {
            'transformed_words': words,
            'encoded_words': result_text,
            'predicted_ratios': ['{:2.2%}'.format(_) for _ in list(predicted)],
        }

