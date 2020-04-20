from __future__ import absolute_import, division, print_function, unicode_literals

import os
from .translator_pinyin import translate_by_string, traceback_by_stringcode
from .chinese_filter_basic import BasicChineseFilter
from dataparser.apps import JieBaDictionary
from ai.models import DigitalVocabulary, SoundVocabulary, NewVocabulary

import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
import pickle




class PinYinFilter(BasicChineseFilter):
    """
    """

    digital_vocabulary_map = {}
    tokenizer_vocabularies = []
    num_status_classs = 8
    max_pinyin_word = 7
    full_vocab_size = 65536
    jieba_dict = None
    encoder = None
    unknown_words = []
    unknown_word_key = 'UNKNOWN_'

    def __init__(self, data = [], load_folder=None):

        self.jieba_dict = JieBaDictionary()
        self.load_new_vocabulary_to_unknown_words()
        
        super().__init__(data=data, load_folder=load_folder)


    def load_new_vocabulary_to_unknown_words(self):
        self.unknown_words = list(NewVocabulary.objects.values_list('pinyin', flat=True))
    

    #override return list
    def transform_str(self, _string):
        # print('transform str: ', _string)
        _pinyin = translate_by_string(_string)
        words, unknowns = self.jieba_dict.split_word(_pinyin)
        if unknowns:
            for _uw in unknowns:
                
                # print("unknowns: ", words)
                # print("unknowns: ", unknowns)
                if _uw not in self.unknown_words:
                    self.unknown_words.append(_uw)
                    _new = NewVocabulary(pinyin=_uw)
                    _new.save()
                    # print('_string: ', _string)
                    print("Pinyin Filter: transform_str unknown word found: ", _uw, ' | ', _string)
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
    def fit_model(self, epochs=5, verbose=1, save_folder=None, train_data=None, validation_data=None, stop_accuracy=None):
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

            # batch_train_data = batch_train_data.shuffle(BUFFER_SIZE, reshuffle_each_iteration=False)
            batch_test_data = batch_train_data.take(VALIDATION_SIZE).shuffle(VALIDATION_SIZE)

        else:
            print('Can Not Give Validation Data.')
            exit(2)

        history = None
        batch_train_data = batch_train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[])).repeat(epochs)
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


    # override
    def load(self, folder):
        print('Starting load model: ', folder)
        self.saved_folder = folder
        self.load_model(folder + '/model.h5')
        self.load_tokenizer_vocabularies()
        
        print('Successful load model. ', folder)

    
    def load_tokenizer_vocabularies(self):
        # with open(self.saved_folder + '/tokenizer_vocabularies.pickle', 'rb') as handle:
        #     self.tokenizer_vocabularies = pickle.load(handle)
            # self.encoder = tfds.features.text.TokenTextEncoder(self.tokenizer_vocabularies)
        vocabulary_length = len(self.jieba_dict.vocabularies)
        assert vocabulary_length > 0
        assert vocabulary_length < self.full_vocab_size
        self.encoder = tfds.features.text.TokenTextEncoder(self.jieba_dict.vocabularies)


    def tokenize_data(self, datalist):
        print('Start Tokenize Data.')
        self.load_tokenizer_vocabularies()
        encoder = self.encoder
        unknowns = self.unknown_words
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

            tokenized.append(_list)
            
            # print('words: ', words)
            # print('next list: ', _list)
        
        
        print('Tokenize Done.')
        
        return tokenized

    
    # override
    def predictText(self, text, lv = 0):
        
        if lv < self.avoid_lv:

            _words = self.transform(text)

            _result_text = self.get_encode_word(_words)

            if len(_result_text) == 0:
                return 0
            
            predicted = self.model.predict([_result_text])[0]
            passible = np.argmax(predicted)

            # print('predicted: ', predicted)
        
        else:

            passible = 0

        return passible


    
    def check_word_unknown(self, _word):
        max_pinyin_word = self.max_pinyin_word
        _word_list = _word.split('_')
        for _ in _word_list:
            if len(_) > max_pinyin_word:
                return False
        return True


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
        _vocal_size = len(self.jieba_dict.vocabularies)

        for _ in _words:

            if not self.check_word_unknown(_):
                _result_text.append(0)
                continue
            
            _loc = self.encoder.encode(_)
            
            if len(_loc) > 0:
                __code = _loc[0]

                if __code > _vocal_size:
                    # find the new word
                    if self.tokenize_data([[_]], save_new_vocabulary=True):
                        _result_text.append(__code)
                    else:
                        _result_text.append(0)
                    
                elif __code > 0:
                    _result_text.append(__code)
        
        return _result_text


    # override
    def get_train_batchs(self):
        
        x, y = self.get_xy_data()
        length_x = len(x)
        assert length_x > 0
        self.length_x = length_x

        tokenized_list = self.tokenize_data(x)

        labeled_dataset = self.bathchs_labeler(tokenized_list, y)

        return labeled_dataset


    # override
    def get_details(self, text):
        words = self.transform(text)
        result_text = self.get_encode_word(words)

        predicted = self.model.predict([result_text])[0]
        return {
            'transformed_words': words,
            'encoded_words': result_text,
            'predicted_ratios': ['{:2.2%}'.format(_) for _ in list(predicted)],
        }
    

    # override
    def get_reason(self, text, prediction):
        reason = ''
        _words = self.transform(text)

        _result_text = self.get_encode_word(_words)

        _res = self.model.predict(_result_text)
        _i = 0
        for _ in _res:
            _max = np.argmax(_)
            if _max == prediction:
                vocabulary = _words[_i]
                reason = self.transform_back_str(vocabulary)
                break
            _i += 1
        
        return reason
