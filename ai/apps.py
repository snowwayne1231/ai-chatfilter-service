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

    code_grammar_delete = 21

    def __init__(self, jieba_vocabulary=[], pinyin_unknown_words=[]):
        print('=============  A.I Init  =============')
        print('using tensorflow version: ', tf.__version__)
        
        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path, jieba_vocabulary=jieba_vocabulary, unknown_words=pinyin_unknown_words)
        self.grammar_model = GrammarFilter(load_folder=grammar_model_path)
    

    def predict(self, txt, lv=0, with_reason=False, no_grammar=False):
        prediction = 0
        reason = ''
        # return 0, ''
        pinyin_prediction = self.pinyin_model.predictText(txt, lv)
        if pinyin_prediction > 0:
            # print('pinyin_prediction: ', pinyin_prediction)
            prediction = pinyin_prediction
            if with_reason:
                reason = self.pinyin_model.get_reason(txt, pinyin_prediction)

                if not reason:
                    reason = txt
        
        elif not no_grammar:
            grammar_prediction = self.grammar_model.predictText(txt, lv)
            prediction = grammar_prediction
            if grammar_prediction > 0 and with_reason:
                reason = 'delted by grammar model'
                prediction = self.code_grammar_delete


        return prediction, reason

    
    def get_details(self, txt):
        if txt:
            _pinyin_detail = self.pinyin_model.get_details(txt)
            _grammer_detail = self.grammar_model.get_details(txt)
            # print('_grammer_detail: ', _grammer_detail)
            
        else:
            _pinyin_detail = {}
            _grammer_detail = {}
            
        return {
            'text': txt,
            'pinyin': _pinyin_detail,
            'grammar': _grammer_detail,
        }

    def get_pinyin_vocabulary(self):
        return self.pinyin_model.get_pure_vocabulary()

    def get_pinyin_unknowns(self):
        return self.pinyin_model.get_unknown_words_and_message()

    def get_path_pinyin(self):
        return self.pinyin_model.get_saved_model_path()

    def get_path_grammar(self):
        return self.grammar_model.get_saved_model_path()


