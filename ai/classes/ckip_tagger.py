from ckiptagger import data_utils, construct_dictionary, WS, POS, NER
import os

class CkipTagger():
    """
    """
    ws = None
    pos = None
    ner = None

    def __init__(self):
        data_path = os.path.dirname(__file__) + '/../assets/ckip_data'
        self.ws = WS(data_path)
        self.pos = POS(data_path)
        self.ner = NER(data_path)

