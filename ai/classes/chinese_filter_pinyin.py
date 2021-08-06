from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re

from ai.service_impact import get_all_vocabulary_from_models
from .translator_pinyin import translate_by_string, traceback_by_stringcode
from .chinese_filter_basic import BasicChineseFilter

import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
import json


class PinYinFilter(BasicChineseFilter):
    """
    """

    widen_lv = 3
    tmp_encoded_text = []

    unknown_words = []
    unknown_words_new_full_message = []

    should_block_list = []
    should_block_pinyin_map = {}
    should_block_shap_list = []

    STATUS_SEPCIFY_BLOCK = 8
    

    def __init__(self, data = [], load_folder=None, jieba_vocabulary=[], jieba_freqs=[],  unknown_words=[]):

        should_be_blocked_exist_words_list = []
        should_be_blocked_pinyin_list = []

        _json_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', 'pinyin_block_list.json')
        with open(_json_file_path, encoding='utf-8') as _file:
            json_data = json.load(_file)
            should_be_blocked_pinyin_list = json_data.get('attached')
            should_be_blocked_exist_words_list = json_data.get('exists')

        for _ in should_be_blocked_pinyin_list:
            _py = translate_by_string(_)
            # print('========', _, ' :: ', _py)
            if _py not in self.should_block_list:
                self.should_block_list.append(_py)
                self.should_block_pinyin_map[_py] = _
            else:
                print('double _ : {}  _py : {}'.format(_, _py))

        # print('should_block_list: ', self.should_block_list)

        self.should_block_shap_list = should_be_blocked_exist_words_list
        self.unknown_words = unknown_words

        if len(jieba_vocabulary) == 0:
            vocabulary_data = get_all_vocabulary_from_models(english=False)
            pinyin_data = vocabulary_data['pinyin']
            for pdata in pinyin_data:
                jieba_vocabulary.append(pdata[0])
                jieba_freqs.append(pdata[1])

        for _sb in self.should_block_list:
            jieba_vocabulary.append(_sb)
            jieba_freqs.append(-1)
        
        super().__init__(data=data, load_folder=load_folder, jieba_vocabulary=jieba_vocabulary, jieba_freqs=jieba_freqs)
        



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
                    print('Find Unknown Word While Transforming: ', _uw)
                    print('  Full Message: ', _string)
                    
        return words


    def transform_back_str(self, _encoded):
        _type = type(_encoded)
        if _type is str:
            return traceback_by_stringcode(_encoded)
        elif _type is list:
            return [self.transform_back_str(_) for _ in _encoded]
        else:
            return _encoded



    def find_block_word(self, word_list = [], text_string = ''):
        _sbl = self.should_block_list
        _sbsl = self.should_block_shap_list
        for _w in word_list:
            if _w in _sbl:
                return self.should_block_pinyin_map.get(_w, _w)

        for _ in _sbsl:
            if isinstance(_, list):
                _num_matched = 0
                for __ in _:
                    if __ in text_string:
                        _num_matched += 1
                
                if _num_matched == len(_):
                    return ''.join(_)
            
            else:
                for _str in text_string:
                    if _str == _:
                        return _str
            
        return ''

    
    # override
    def predictText(self, text, lv = 0):
        _words = self.transform(text)
        if len(_words) == 0:
            return 0
        
        # check static block word list
        _blocked_word = self.find_block_word(_words, text)
        if _blocked_word:
            return self.STATUS_SEPCIFY_BLOCK
        
        _result_text, _has_unknown = self.get_encode_word(_words)

        if len(_result_text) == 0:
            return 0

        # save to tmp do not need reencode when get details
        if len(self.tmp_encoded_text) >= 3:
            self.tmp_encoded_text = self.tmp_encoded_text[-2:]
        self.tmp_encoded_text.append([text, _result_text])

           
        predicted = self.model(np.array([_result_text]))[0]
        # print('predicted: ', predicted)

        possible = np.argmax(predicted)

        # should be delete and lv over power
        if possible > 0:
            _lv_disparity = lv - self.widen_lv + 1
            _ratio_zero = predicted[0]
            _ratio_predict = predicted[possible]
            if _lv_disparity > 0:
                _ratio_lv_plus = _lv_disparity * 0.15

                if (_ratio_zero + _ratio_lv_plus) > _ratio_predict:
                    possible = 0
                
            # elif len(_words) < 2:
            #     _ratio_plus = 0.25
            #     if (_ratio_zero + _ratio_plus) > _ratio_predict:
            #         possible = 0
        return possible



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
            'transformed_words': self.transform(text)
        }
    

    # override
    def get_reason(self, text, prediction):
        reason = ''
        tmp = self.tmp_encoded_text
        encoded_words = []
        for _ in tmp:
            if text == _[0]:
                encoded_words = _[1]

        if encoded_words:
            if prediction == self.STATUS_SEPCIFY_BLOCK:
                reason = self.find_block_word(self.transform(text), text)
                return reason
            
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
    






class PinYinReverseStateFilter(PinYinFilter):
    """
        Extend By PinYinFilter
        Add State Code Reverse To Cover Unknow Prediction to 0
        And Give a New State to return result
    """
    STATE_OF_PASS = 7
    STATE_UNKNOWN_MEANING = 9
    PASS_RATIO = 0.999
    # override
    def set_data(self, data):
        if self.check_data_shape(data):
            index_status = self.columns.index('STATUS')
            # _new_data = []
            _state_of_pass = self.STATE_OF_PASS
            for d in data:
                 if d[index_status] == 0:
                    d[index_status] = _state_of_pass

            self.data = data
            self.data_length = len(data)

            # self.split_word('TEXT')
            self.transform_column('TEXT')

        else:
            
            print('Set data failed.')
            return False

        return self

    # override
    def predictText(self, text, lv=0):
        _words = self.transform(text)
        if len(_words) == 0:
            return 0
        
        _result_text, _has_unknown = self.get_encode_word(_words)

        if len(self.tmp_encoded_text) >= 3:
            self.tmp_encoded_text = self.tmp_encoded_text[-2:]

        self.tmp_encoded_text.append([text, _result_text])

        
        if len(_result_text) == 0:
            return 0
        else:
            _blocked_word = self.find_block_word(_words, text)
            if _blocked_word:
                return self.STATUS_SEPCIFY_BLOCK
        
        predicted = self.model(np.array([_result_text]))[0]
        possible = np.argmax(predicted)

        if possible == self.STATE_OF_PASS and predicted[self.STATE_OF_PASS] > self.PASS_RATIO:
            _others_ratio = 1 - self.PASS_RATIO
            for _p in predicted[:self.STATE_OF_PASS]:
                if _p > _others_ratio:
                    return self.STATE_UNKNOWN_MEANING
            return 0
        elif possible == 0 and lv <= self.widen_lv:
            return self.STATE_UNKNOWN_MEANING

        _lv_disparity = lv - self.widen_lv + 1
        _ratio_zero = predicted[self.STATE_OF_PASS]
        _ratio_predict = predicted[possible]

        if _lv_disparity > 0:
            _ratio_lv_plus = _lv_disparity * 0.15

            if (_ratio_zero + _ratio_lv_plus) > _ratio_predict:
                possible = 0
        return possible
                
        
