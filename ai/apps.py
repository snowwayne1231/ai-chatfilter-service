from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path, get_grammar_path
from .classes.chinese_filter_pinyin import PinYinFilter
from .classes.chinese_filter_grammar import GrammarFilter

import tensorflow as tf

pinyin_model_path = get_pinyin_path()
grammar_model_path = get_grammar_path()

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():
    pinyin_model = None
    grammar_model = None

    loaded_models = []
    loaded_model_names = []

    def __init__(self):
        print('=============  A.I Init  =============')
        print('using tensorflow version: ', tf.__version__)


    def load_pinyin(self, jieba_vocabulary=[], pinyin_unknown_words=[], jieba_freqs=[]):
        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path, jieba_vocabulary=jieba_vocabulary, unknown_words=pinyin_unknown_words, jieba_freqs=jieba_freqs)
        self.loaded_models.append(self.pinyin_model)
        self.loaded_model_names.append('pinyin')


    def load_garmmar(self):
        self.grammar_model = GrammarFilter(load_folder=grammar_model_path)
        self.loaded_models.append(self.grammar_model)
        self.loaded_model_names.append('grammar')
    

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


    def get_pinyin_vocabulary(self):
        return self.pinyin_model.get_pure_vocabulary() if self.pinyin_model else []

    def get_pinyin_freqs(self):
        return self.pinyin_model.get_vocabulary_freq() if self.pinyin_model else []

    def get_pinyin_unknowns(self):
        return self.pinyin_model.get_unknown_words_and_message() if self.pinyin_model else []



