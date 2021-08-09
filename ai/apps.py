from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path, get_grammar_path, get_english_model_path, get_pinyin_re_path
from .classes.chinese_filter_pinyin import PinYinFilter, PinYinReverseStateFilter
from .classes.chinese_filter_grammar import GrammarFilter
from .classes.english_filter_basic import BasicEnglishFilter

import tensorflow as tf

pinyin_model_path = get_pinyin_path()
pinyin_model_re_path = get_pinyin_re_path()
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


    def load_pinyin(self, folder=None, is_version_of_reverse=False):
        _jieba_vocabulary = [_[0] for _ in self.pinyin_data]
        _jieba_freqs = [_[1] for _ in self.pinyin_data]
        print('is_version_of_reverse: ', is_version_of_reverse)
        if is_version_of_reverse:
            _pinyin_model_path = folder if folder else pinyin_model_re_path
            self.pinyin_model = PinYinReverseStateFilter(load_folder=_pinyin_model_path, jieba_vocabulary=_jieba_vocabulary, unknown_words=[], jieba_freqs=_jieba_freqs)
        else:
            _pinyin_model_path = folder if folder else pinyin_model_path
            self.pinyin_model = PinYinFilter(load_folder=_pinyin_model_path, jieba_vocabulary=_jieba_vocabulary, unknown_words=[], jieba_freqs=_jieba_freqs)

        self.loaded_models.append(self.pinyin_model)
        self.loaded_model_names.append('pinyin')


    def load_garmmar(self, folder=None):
        _grammar_model_path = folder if folder else grammar_model_path
        self.grammar_model = GrammarFilter(load_folder=_grammar_model_path)
        self.loaded_models.append(self.grammar_model)
        self.loaded_model_names.append('grammar')


    def load_english(self, folder=None):
        # print('[load_english]: english_data: ', self.english_data)
        _english_model_apth = folder if folder else english_model_apth
        _english_vocabulary = [_[0] for _ in self.english_data]
        self.english_model = BasicEnglishFilter(load_folder=_english_model_apth, english_vocabulary=_english_vocabulary)
        self.loaded_models.append(self.english_model)
        self.loaded_model_names.append('english')


    def load_bert(self, folder=None):
        # _path = folder if folder else model_apth
        model = None
        self.loaded_models.append(model)
        self.loaded_model_names.append('bert')
    

    def predict(self, txt, lv=0, with_reason=False):
        prediction = 0
        reason = ''

        for model in self.loaded_models:
            _predict, reason = model.predictText(txt, lv, with_reason=with_reason)
            if _predict > 0:
                prediction = _predict
                break

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



