from django.apps import AppConfig
import tensorflow as tf
from tensorflow import keras
import tensorflow_datasets as tfds

print('using tensorflow version: ', tf.__version__)

class AiConfig(AppConfig):
    name = 'ai'



class MainAiApp():


    def __init__(self):
        print('============= AI MainAiApp =============')
        
        (train_data, test_data), info = tfds.load(
            # Use the version pre-encoded with an ~8k vocabulary.
            'imdb_reviews/subwords8k', 
            # Return the train/test datasets as a tuple.
            split = (tfds.Split.TRAIN, tfds.Split.TEST),
            # Return (example, label) pairs from the dataset (instead of a dictionary).
            as_supervised=True,
            # Also return the `info` structure. 
            with_info=True)

        print('== train_data ==')
        print(train_data)