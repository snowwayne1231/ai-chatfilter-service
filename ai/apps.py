from django.apps import AppConfig
from tensorflow import keras
from .helper import get_pinyin_path
from .classes.pinyin import PinYinFilter

import tensorflow as tf

pinyin_model_path = get_pinyin_path()

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():
    pinyin_model = None

    def __init__(self):
        print('============= AI MainAiApp =============')
        print('using tensorflow version: ', tf.__version__)
        self.pinyin_model = PinYinFilter(load_folder=pinyin_model_path)
        
    def predict(self, txt):
        print('MainAiApp predict txt : ', txt)
        pinyin_prediction = self.pinyin_model.predictText(txt)
        return pinyin_prediction
        