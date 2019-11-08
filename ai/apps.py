from django.apps import AppConfig
import tensorflow as tf
from tensorflow import keras

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():


    def __init__(self):
        print('============= AI MainAiApp =============')
        print('using tensorflow version: ', tf.__version__)
        
        