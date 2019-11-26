from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path
from .classes.pinyin import PinYinFilter
from .classes.ckip_tagger import CkipTagger

import tensorflow as tf

pinyin_model_path = get_pinyin_path()

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():
    pinyin_model = None
    # ckip_tagger = None

    def __init__(self):
        print('============= AI MainAiApp =============')
        print('using tensorflow version: ', tf.__version__)
        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path)
        # self.ckip_tagger = CkipTagger()
    

    def predict(self, txt, lv=0, silence=False):
        reason = ''
        # return 0, ''
        pinyin_prediction = self.pinyin_model.predictText(txt, lv)
        if pinyin_prediction > 0:
            # print('pinyin_prediction: ', pinyin_prediction)
            # reason = self.pinyin_model.get_reason(txt, pinyin_prediction)
            pass
        if silence:
            pass
        else:
            print('MainAiApp predict txt: ', txt)
            print('Prediction reason: ', reason)

        return pinyin_prediction, reason

