from __future__ import absolute_import, division, print_function, unicode_literals

from .chinese_filter_basic import BasicChineseFilter
from ai.models import Vocabulary, Language

import tensorflow as tf
import tensorflow_datasets as tfds
import os, re
import numpy as np
from datetime import datetime, timedelta




class BasicEnglishFilter(BasicChineseFilter):
    """
    """

    re_is_chinese = re.compile('[\u4e00-\u9fa5]')
    re_is_english = re.compile('[a-zA-Z]')
    re_is_number = re.compile('[0-9]')
    re_is_other = re.compile('[\u0020-\u0085]')

    status_classsets = 4
    full_words_length = 255

    basic_num_dataset = 5000

    eng_vocabulary = []
    freqs = []
    encoder = None

    def __init__(self, data = [], load_folder=None, english_vocabulary=[]):

        if english_vocabulary:
            self.eng_vocabulary = english_vocabulary
        else:
            _lan = Language.objects.filter(code='EN').first()
            _model_vocabulary = Vocabulary.objects.filter(language=_lan)
            self.eng_vocabulary = list(_model_vocabulary)

        print('[BasicEnglishFilter] eng_vocabulary: ', self.eng_vocabulary)

        self.encoder = tfds.features.text.TokenTextEncoder(self.eng_vocabulary)
        
        super().__init__(data=data, load_folder=load_folder)
    

    # override return list
    def transform_str(self, _string):
        return re.split(r'[\s]+', _string)

    
    # override
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.status_classsets

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, all_scs, mask_zero=True))
        # model.add(tf.keras.layers.Flatten())
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs)))
        model.add(tf.keras.layers.GlobalAveragePooling1D())
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs, return_sequences=True)))
        # model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
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


    # override
    def fit_model(self, epochs=3, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None, stop_hours=None):
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
            _start = datetime.now()
            if stop_hours:
                _end = _start + timedelta(hours=stop_hours)
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
                
                if stop_hours:
                    _now = datetime.now()
                    if _now > _end:
                        break
                
        except KeyboardInterrupt:
            print('Keyboard pressed. Stop Tranning.')
        except Exception as err:
            print('Exception on Fit model.')
            print('Exception Message: {}'.format(err))
        
        return history

    

    def get_train_batchs(self, check_duplicate= True):
        
        x, y = self.get_xy_data()

        _parsed_x_list = [ self.parse_texts(_) for _ in x ]

        if check_duplicate:

            _i = 0
            _check_map = {}
            _check_map_idx = {}
            _all_duplicate_zipstr = []

            for _ in _parsed_x_list:
                _zip_str = '|'.join(str(__) for __ in _)
                _map_value = _check_map.get(_zip_str, None)
                _y_value = 0 if y[_i] == 0 else 1
                # print(_i, ': ', [self.transform_back_str(xx) for xx in x[_i]], _)

                if _map_value:
                    if _map_value != _y_value:
                        if _zip_str not in _all_duplicate_zipstr:
                            _all_duplicate_zipstr.append(_zip_str)

                        _origin = self.data[_i][2]
                        _transformed = x[_i]
                        _against_idx = _check_map_idx[_zip_str]
                        _against = self.data[_against_idx][2]
                        print('[Grammarly Filter][get_train_batchs] Duplicate Data: {} | Idx: {} | against: {} | {}'.format(_origin, _i, _against_idx, _against))
                        
                    
                else:
                    _check_map[_zip_str] = _y_value
                    _check_map_idx[_zip_str] = _i
                
                _i += 1

            if len(_all_duplicate_zipstr) > 0:
                print('[Error] Failed To Start Train Because Data is Confusion.')
                exit(2)
        
        _basic = int(self.basic_num_dataset / len(x))

        if _basic >= 1:
            _parsed_x_list = _parsed_x_list * (_basic+1)
            y = y * (_basic+1)

        self.length_x = len(_parsed_x_list)

        _full_wl = self.full_words_length

        def gen():
            for idx, texts in enumerate(_parsed_x_list):
                if len(texts) == 0:
                    continue

                st = 1 if y[idx] and int(y[idx]) > 0 else 0
                
                yield texts, st

        dataset = tf.data.Dataset.from_generator(
            gen,
            ( tf.int32, tf.int32 ),
            ( tf.TensorShape([_full_wl, ]), tf.TensorShape([]) ),
        )

        return dataset


    def load_tokenizer_vocabularies(self):
        _vocabularies = self.jieba_dict.get_vocabulary()
        vocabulary_length = len(_vocabularies)
        # print('[load_tokenizer_vocabularies] vocabulary_length: ', vocabulary_length)
        assert vocabulary_length > 0
        assert vocabulary_length < self.full_vocab_size
        # print('[load_tokenizer_vocabularies] _vocabularies: ', _vocabularies)
        self.tokenizer_vocabularies = _vocabularies
        self.encoder = tfds.features.text.TokenTextEncoder(_vocabularies)
        self.encoder_size = vocabulary_length


    def parse_texts(self, texts):
        # next_txt = []
        # _len = len(texts)
        _max_length = self.full_words_length
        
        return np.array(texts[:_max_length])


    # override
    def get_details(self, text):

        _words = self.transform(text)

        if len(_words) == 0:
            return 0

        _texts = self.parse_texts(_words)

        # print('predictText  _words : ', _words, _words.shape)
        
        predicted = self.model.predict(np.array([_texts]))[0]

        # print('grammar predicted: ', predicted)

        return {
            'grammar_words': _words,
            'predicted_ratios': ['{:2.2%}'.format(_) for _ in list(predicted)],
        }
    

    # override
    def predictText(self, text, lv = 0):
        
        if lv < self.avoid_lv:

            _words = self.transform(text)

            if len(_words) == 0:
                return 0

            _words = self.parse_texts(_words)

            # print('predictText  _words : ', _words, _words.shape)
            
            predicted = self.model.predict(np.array([_words]))[0]
            passible = np.argmax(predicted)
            
            if passible > 0:
                passible = self.CODE_DELETED

            # print('predicted: ', predicted)
            # print('passible: ', passible)
        
        else:

            passible = 0

        return passible

    
    # override
    def get_reason(self, text, prediction):
        return 'Deleted by grammar filter.'
