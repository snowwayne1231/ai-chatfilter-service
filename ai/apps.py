from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path
from .classes.chinese_filter_pinyin import PinYinFilter

import tensorflow as tf

pinyin_model_path = get_pinyin_path()

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():
    pinyin_model = None

    def __init__(self):
        print('=============  A.I Init  =============')
        print('using tensorflow version: ', tf.__version__)
        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path)
    

    def predict(self, txt, lv=0, silence=False):
        reason = ''
        # return 0, ''
        pinyin_prediction = self.pinyin_model.predictText(txt, lv)
        if pinyin_prediction > 0:
            # print('pinyin_prediction: ', pinyin_prediction)
            if not silence:
                reason = self.pinyin_model.get_reason(txt, pinyin_prediction)
        # if silence:
        #     pass
        # else:
        #     print('MainAiApp predict txt: ', txt)
        #     print('Prediction reason: ', reason)

        return pinyin_prediction, reason

    
    def get_details(self, txt):
        return self.pinyin_model.get_details(txt) if txt else {}

