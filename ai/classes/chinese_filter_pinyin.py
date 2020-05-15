from __future__ import absolute_import, division, print_function, unicode_literals

import os
from .translator_pinyin import translate_by_string, traceback_by_stringcode
from .chinese_filter_basic import BasicChineseFilter
from dataparser.apps import JieBaDictionary
# from ai.models import NewVocabulary

import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
import pickle
from datetime import datetime, timedelta




class PinYinFilter(BasicChineseFilter):
    """
    """

    digital_vocabulary_map = {}
    tokenizer_vocabularies = []
    num_status_classs = 8
    full_vocab_size = 65536
    jieba_dict = None
    basic_num_dataset = 5000

    encoder = None
    encoder_size = 0
    tmp_encoded_text = []

    unknown_words = []
    unknown_words_new_full_message = []
    unknown_position = 0
    

    def __init__(self, data = [], load_folder=None, unknown_words=[], jieba_vocabulary=[]):

        self.jieba_dict = JieBaDictionary(vocabulary=jieba_vocabulary)
        self.unknown_position = self.jieba_dict.get_unknown_position()
        if len(unknown_words) == 0:
            pass
        else:
            self.unknown_words = unknown_words
        
        super().__init__(data=data, load_folder=load_folder)
    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        
        words, unknowns = self.jieba_dict.split_word(_pinyin)
        # print(_string, ', ', words, ', uk: ' , unknowns)
        
        if unknowns:
            # print("transform_str unknowns: ", unknowns)
            for _uw in unknowns:
                
                # print("unknowns: ", words)
                
                if _uw not in self.unknown_words:
                    self.unknown_words.append(_uw)
                    self.unknown_words_new_full_message.append([_uw, _string])
                    # _new = NewVocabulary(pinyin=_uw, text=_string[:64])
                    # _new.save()
                    # print('_string: ', _string)
                    # print("Pinyin Filter: transform_str [] unknown word found: ", _uw, ' | ', _string)
        # print(_pinyin)
        # print(words)
        return words


    def transform_back_str(self, _encoded):
        _type = type(_encoded)
        if _type is str:
            return traceback_by_stringcode(_encoded)
        elif _type is list:
            return [self.transform_back_str(_) for _ in _encoded]
        else:
            return _encoded


    # override
    def build_model(self):
        full_words_length = self.full_words_length
        all_scs = self.num_status_classs

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Embedding(self.full_vocab_size, all_scs))
        # model.add(tf.keras.layers.Flatten())
        model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs)))
        model.add(tf.keras.layers.Dense(full_words_length, activation=tf.nn.relu))
        # model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(all_scs, return_sequences=True)))
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


    # override
    def fit_model(self, epochs=5, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None, stop_hours=None):
        if save_folder is not None:
            self.saved_folder = save_folder
        
        if train_data is not None:
            self.set_data(train_data)

        # return exit(2)
        batch_train_data = self.get_train_batchs()

        _length_of_data = self.length_x

        BUFFER_SIZE = _length_of_data + 1
        BATCH_SIZE = self.full_words_length
        VALIDATION_SIZE = int(_length_of_data / 8) if _length_of_data > 5000 else int(_length_of_data / 2)

        if validation_data is None:

            batch_train_data = batch_train_data.shuffle(BUFFER_SIZE, reshuffle_each_iteration=True).repeat(epochs)
            batch_test_data = batch_train_data.take(VALIDATION_SIZE).shuffle(VALIDATION_SIZE, reshuffle_each_iteration=True)

        else:
            print('Can Not Give Validation Data.')
            exit(2)

        history = None
        batch_train_data = batch_train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))
        batch_test_data = batch_test_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

        # print(batch_train_data)
        # for __ in batch_train_data.take(1):
        #     print(__)

        print('==== batch_train_data ====')
        print('Length of Data :: ', _length_of_data)
        print('BUFFER_SIZE :: ', BUFFER_SIZE)
        print('BATCH_SIZE :: ', BATCH_SIZE)
        print('VALIDATION_SIZE :: ', VALIDATION_SIZE)

        # exit(2)

        steps = int(_length_of_data / BATCH_SIZE)
        vaildation_steps = int(VALIDATION_SIZE / BATCH_SIZE)

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
        except Exception:
            print('Exception on Fit model.')
        
        return history


    # override
    def load(self, folder):
        print('Starting load model: ', folder)
        self.saved_folder = folder
        self.load_model(folder + '/model.h5')
        self.load_tokenizer_vocabularies()
        
        print('Successful load model: ', folder)

    
    def load_tokenizer_vocabularies(self):
        _vocabularies = self.jieba_dict.get_vocabulary()
        vocabulary_length = len(_vocabularies)
        assert vocabulary_length > 0
        assert vocabulary_length < self.full_vocab_size
        self.tokenizer_vocabularies = _vocabularies
        self.encoder = tfds.features.text.TokenTextEncoder(_vocabularies)
        self.encoder_size = vocabulary_length


    def tokenize_data(self, datalist):
        print('Start Tokenize Data.')
        self.load_tokenizer_vocabularies()
        encoder = self.encoder
        # unknowns = self.unknown_words
        _i = 0
        _total = len(datalist)
        tokenized = []

        def get_encode(text):
            encoded_list = encoder.encode(text)
            if len(encoded_list) > 0:
                return encoded_list[0]
            else:
                return 0

        # print(datalist[:10])
        
        for words in datalist:
            _i += 1
            if _i % 1000 == 0:
                _percent = _i / _total * 100
                print(" {:.2f}%".format(_percent), end="\r")

            _list = []
            for word in words:
                _list.append(get_encode(word))

            if _list and len(_list) >0:
                tokenized.append(_list)
            
            # print('words: ', words)
            # print('next list: ', _list)
        
        
        print('Tokenize Done.')
        
        return tokenized

    
    # override
    def predictText(self, text, lv = 0):

        _words = self.transform(text)

        if len(_words) == 0:
            return 0

        _lv_disparity = lv - self.avoid_lv
        
        _result_text = self.get_encode_word(_words)
        
        
        if len(_result_text) == 0:
            print('[predictText] | No result text: {},  words: {},  length: {}'.format(text, _words, len(text)))
            return 0

        if len(self.tmp_encoded_text) > 3:
            self.tmp_encoded_text = self.tmp_encoded_text[:3]

        self.tmp_encoded_text.append([text, _result_text])

        predicted = self.model.predict([_result_text])[0]
        # print('predicted: ', predicted)

        possible = np.argmax(predicted)
        # print('possible: ', possible)

        # should be delete and lv over power
        if _lv_disparity > 0 and possible > 0:
            
            _ratio_zero = predicted[0]
            _ratio_predict = predicted[possible]
            _ratio_lv_plus = _lv_disparity * 0.15

            if (_ratio_zero + _ratio_lv_plus) > _ratio_predict:
                possible = 0

        return possible


    def bathchs_labeler(self, x, y):
        assert len(x) == len(y)
        encoder = self.encoder
        full_words_length = self.full_words_length

        def gen():
            for idx, texts in enumerate(x):
                _len = len(texts)
                if _len == 0:
                    continue

                st = y[idx] if y[idx] else 0
                npts = np.pad(texts, (0, full_words_length - _len), 'constant')

                yield npts, np.int64(st)
                # yield npts, [0,0,0,0,0,0,0,0]
        
        dataset = tf.data.Dataset.from_generator(
            gen,
            ( tf.int64, tf.int64 ),
            ( tf.TensorShape([full_words_length]), tf.TensorShape([]) ),
        )

        # print(dataset)
        # for __ in dataset.take(10):
        #     print(__)
        # exit(2)
        return dataset


    def get_encode_word(self, _words):
        _result_text = []
        _encoder = self.encoder
        _max_size = self.encoder_size

        for _ in _words:
            
            _loc = _encoder.encode(_)
            
            if len(_loc) > 0:
                __code = _loc[0]

                if __code > _max_size:
                    # find the new word
                    print('[Pinyin filter][get_encode_word] | unknown encode word: {},  _words: {}'.format(_, _words))
                    _result_text.append(self.unknown_position)
                    
                elif __code >= 0:
                    _result_text.append(__code)
        
        return _result_text


    # override
    def get_train_batchs(self):
        
        x, y = self.get_xy_data()

        tokenized_list = self.tokenize_data(x)

        _basic = int(self.basic_num_dataset / len(tokenized_list))

        if _basic >= 1:
            tokenized_list = tokenized_list * (_basic+1)
            y = y * (_basic+1)

        self.length_x = len(tokenized_list)

        labeled_dataset = self.bathchs_labeler(tokenized_list, y)

        return labeled_dataset


    # override
    def get_details(self, text):
        tmp = self.tmp_encoded_text
        encoded_words = []
        for _ in tmp:
            if text == _[0]:
                encoded_words = _[1]

        if encoded_words:
            predicted = self.model.predict([encoded_words])[0]
        else:
            predicted = []

        # print('encoded_words: ', encoded_words)
        
        return {
            'decodes': [self.get_decode_str(_) for _ in encoded_words],
            'encoded_words': encoded_words,
            'predicted_ratios': ['{:2.2%}'.format(_) for _ in list(predicted)],
        }
    

    # override
    def get_reason(self, text, prediction):
        reason = ''
        tmp = self.tmp_encoded_text
        encoded_words = []
        for _ in tmp:
            if text == _[0]:
                encoded_words = _[1]

        _res = self.model.predict(encoded_words)
        _i = 0
        # print('encoded_words: ', encoded_words)
        for _ in _res:
            _max = np.argmax(_)
            if _max == prediction:
                # vocabulary = _words[_i]
                # reason = self.transform_back_str(vocabulary)
                _icode = encoded_words[_i]
                reason = self.get_decode_str(_icode)
                break
            _i += 1
        
        return reason


    def get_decode_str(self, code):
        _pinyin = self.tokenizer_vocabularies[code-1] if len(self.tokenizer_vocabularies) >= code else None
        if _pinyin:
            return self.transform_back_str(_pinyin)
        else:
            return ''


    def get_pure_vocabulary(self):
        return self.jieba_dict.get_vocabulary(pure=True)

    def get_unknown_words_and_message(self):
        return self.unknown_words_new_full_message
        
