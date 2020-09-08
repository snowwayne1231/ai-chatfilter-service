from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path, get_grammar_path, get_english_model_path
from .classes.chinese_filter_pinyin import PinYinFilter
from .classes.chinese_filter_grammar import GrammarFilter
from .classes.english_filter_basic import BasicEnglishFilter

import tensorflow as tf

pinyin_model_path = get_pinyin_path()
grammar_model_path = get_grammar_path()
english_model_apth = get_english_model_path()

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():
    pinyin_model = None
    grammar_model = None
    english_model = None

    pinyin_data = []
    english_data = []

    loaded_models = []
    loaded_model_names = []

    def __init__(self, pinyin_data=[], english_data=[]):
        print('=============  A.I Init  =============')

        if pinyin_data:
            self.pinyin_data = pinyin_data

        if english_data:
            self.english_data = english_data
        
        print('using tensorflow version: ', tf.__version__)


    def load_pinyin(self):
        _jieba_vocabulary = [_[0] for _ in self.pinyin_data]
        _jieba_freqs = [_[1] for _ in self.pinyin_data]

        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path, jieba_vocabulary=_jieba_vocabulary, unknown_words=[], jieba_freqs=_jieba_freqs)
        self.loaded_models.append(self.pinyin_model)
        self.loaded_model_names.append('pinyin')


    def load_garmmar(self):
        self.grammar_model = GrammarFilter(load_folder=grammar_model_path)
        self.loaded_models.append(self.grammar_model)
        self.loaded_model_names.append('grammar')


    def load_english(self):
        # print('[load_english]: english_data: ', self.english_data)
        _english_vocabulary = [_[0] for _ in self.english_data]
        self.english_model = BasicEnglishFilter(load_folder=english_model_apth, english_vocabulary=_english_vocabulary)
        self.loaded_models.append(self.english_model)
        self.loaded_model_names.append('english')
    

    def predict(self, txt, lv=0, with_reason=False):
        prediction = 0
        reason = ''

        for model in self.loaded_models:
            _predict = model.predictText(txt, lv)
            if _predict > 0:
                prediction = _predict
                if with_reason:
                    reason = model.get_reason(txt, _predict)
                    if not reason:
                        reason = txt

        return prediction, reason

    
    def get_details(self, txt):
        details_result = {'text': txt}
        if txt:
            _i = 0
            for model in self.loaded_models:
                _detail = model.get_details(txt)
                details_result[self.loaded_model_names[_i]] = _detail
                _i += 1

        return details_result



