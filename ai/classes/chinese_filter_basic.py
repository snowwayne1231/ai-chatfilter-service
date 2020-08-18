from __future__ import absolute_import, division, print_function, unicode_literals

# from copy import deepcopy

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
# import json
# import sys
import os



class BasicChineseFilter():
    """
    """

    columns = ['ROOM', 'ACCOUNT', 'MESSAGE', 'STATUS', 'TEXT', 'LV', 'ANCHOR']
    appended_columns = ['TRANSFORMED_WORD']
    data = []
    data_length = 0
    model = None

    saved_folder = None
    
    full_words_length = 64
    status_classsets = 8
    avoid_lv = 3
    length_x = 0

    
    def __init__(self, data = [], load_folder=None):
        
        if len(data) > 0:
            
            if not self.set_data(data):
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
            self.data_length = len(data)

            # self.split_word('TEXT')
            self.transform_column('TEXT')

        else:
            
            print('Set data failed.')
            return False

        return self


    def save(self, folder = None, is_check = False):
        if folder is not None:
            self.saved_folder = folder
        elif self.saved_folder:
            folder = self.saved_folder
        else:
            print('Error Save, because folder is not specify')
            return None
        
        if not os.path.isdir(folder) or not os.path.exists(folder):
            os.makedirs(folder)
        
        if not is_check:
            self.save_model(folder + '/model.h5')
        
            print('Successful saved. ')

        return self



    def load(self, folder):
        if folder:
            self.saved_folder = folder

        model_path = self.get_model_path()
        
        print('Starting load model: ', model_path)
        
        self.load_model(model_path)
        
        print('Successful load model. ', model_path)
        

    def save_model(self, path):
        return self.model.save(path)


    def load_model(self, path):
        if os.path.exists(path):
            self.model = tf.keras.models.load_model(path)
        else:
            self.build_model()

        return self.model



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
        _length_of_data = len(self.data)
        _i = 0

        print('Start Transform Data..')

        for d in self.data:
            _text = d[column_idx]
            _transformed_words = self.transform(_text)

            if len(d) == _length_of_columns:
                d[_transformed_idx] = _transformed_words
            else:
                d.append(_transformed_words)

            _i += 1
            if _i % 200 == 0:
                print(' {:.2f}%'.format(_i / _length_of_data * 100), end='\r')

        print('Transform Data Done.')

        return self


    # should be override
    def transform_str(self, _string):
        return _string


    # could be override
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.status_classsets

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        model.add(tf.keras.layers.Dense(all_scs, activation=tf.nn.softmax))

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


    # could be overreide
    def fit_model(self, epochs=1, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None, stop_hours=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)


        batch_train_data = self.get_train_batchs()

        _length_of_data = self.length_x

        BUFFER_SIZE = _length_of_data + 1
        BATCH_SIZE = self.full_words_length
        VALIDATION_SIZE = int(_length_of_data / 8) if _length_of_data > 5000 else int(_length_of_data / 3)

        # exit(2)

        if validation_data is None:

            batch_train_data = batch_train_data.shuffle(BUFFER_SIZE, reshuffle_each_iteration=False)
            batch_test_data = batch_train_data.take(VALIDATION_SIZE)

            # batch_train_data = batch_train_data.skip(VALIDATION_SIZE)
            # _length_of_data -= VALIDATION_SIZE

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



    def get_xy_data(self):
        print('Starting get XY data..', end='\r')
        _full_columns = self.columns + self.appended_columns
        # x_idx = self.columns.index('TEXT') if 'TEXT' in self.columns else -1
        x_idx = _full_columns.index('TRANSFORMED_WORD') if 'TRANSFORMED_WORD' in _full_columns else -1
        vip_lv_idx = _full_columns.index('LV') if 'LV' in _full_columns else -1
        y_idx = _full_columns.index('STATUS') if 'STATUS' in _full_columns else -1
        new_x = []
        new_y = []
        __auto_human_delete_if_not = 3

        data_length = self.data_length
        _i = 0
        _has_not_word_value = False

        for _d in self.data:
            _t = _d[x_idx]
            if _t:
                _status = _d[y_idx]
                if _status:
                    _status = int(_status)
                else:
                    continue
                _vip_lv = _d[vip_lv_idx]
                # if _vip_lv < self.avoid_lv or _status > 0:
                new_x.append(_t)
                new_y.append(_status if _status != '' else __auto_human_delete_if_not)
            else:
                _has_not_word_value = True
                print('[get_xy_data] Not Found: ', _d)

            if _i % 1000 == 0:
                _percent = _i / data_length
                print("Getting XY data processing [{:2.1%}]".format(_percent), end="\r")

            _i += 1
        
        print("Getting XY data sets is done. Total count: ", len(new_x))
        if _has_not_word_value:
            exit(2)
        return new_x, new_y


    # could be override
    def get_train_batchs(self):
        
        x, y = self.get_xy_data()
        length_x = len(x)
        assert length_x > 0
        self.length_x = length_x

        def gen():
            for idx, texts in enumerate(x):
                next_texts = []
                st = y[idx] if y[idx] else 0

                for text in texts:
                    next_texts.append(text)
                    
                yield next_texts, st

        dataset = tf.data.Dataset.from_generator(
            gen,
            ( tf.int64, tf.int64 ),
            ( tf.TensorShape([None]), tf.TensorShape([]) ),
        )

        return dataset


    def predictText(self, text):
        predicted = self.model.predict([text])[0]
        passible = np.argmax(predicted)
        return passible



    def get_reason(self, text, prediction):
        reason = ''
        return reason


    
    def get_details(self, text):
        words = self.transform(text)
        predicted = self.model.predict([words])[0]

        return {
            'transformed_words': words,
            'predicted_ratios': ['{:2.2%}'.format(_) for _ in list(predicted)],
        }


    def get_saved_folder(self):
        return self.saved_folder


    def get_model_path(self):
        return self.get_saved_folder() + '/model.h5'

