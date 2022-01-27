from django.utils import timezone
from django.conf import settings
from django.forms.models import model_to_dict
# from django.core.files.base import ContentFile
from http.client import HTTPConnection
from ai.apps import MainAiApp
from ai.service_impact import get_all_vocabulary_from_models
from ai.helper import get_pinyin_path, get_grammar_path, get_english_model_path, get_pinyin_re_path, get_vocabulary_dictionary_path
from ai.classes.translator_pinyin import translate_by_string

import numpy as np
import time, re, logging, json, urllib
from os import path, listdir

# from .models import GoodSentence




class TwiceMainService():
    """

    """
    service_data = {}
    service_addr = ''
    service_web_port = 80
    service_tcpsocket_port = 8025
    
    STATUS_PREDICTION_NO_MSG = 0
    STATUS_PREDICTION_ADVERTISING = 1
    STATUS_PREDICTION_HUMAN_DELETE = 3
    STATUS_PREDICTION_DIRTY_WORD = 4
    STATUS_PREDICTION_OTHER_AI = 5
    STATUS_PREDICTION_SEPCIFY_BLOCK = 8
    STATUS_PREDICTION_UNKNOWN_MEANING = 9
    STATUS_PREDICTION_SPECIAL_CHAR = 11
    STATUS_PREDICTION_NONSENSE = 12
    STATUS_PREDICTION_WEHCAT_SUSPICION = 13
    STATUS_PREDICTION_BLOCK_WORD = 14
    STATUS_PREDICTION_SUSPECT_WATER_ARMY = 15
    STATUS_PREDICTION_NOT_ALLOW = 16
    STATUS_PREDICTION_SAME_LOGINNAME_IN_SHORTTIME = 17
    STATUS_PREDICTION_GRAMMARLY = 21

    STATUS_MODE_CHINESE = 1
    STATUS_MODE_ENGLISH = 2
    STATUS_MODE_BERT = 3

    REMOTE_ROUTE_PINYIN_MODEL = '/api/model/pinyin'
    REMOTE_ROUTE_GARMMAR_MODEL = '/api/model/grammar'
    REMOTE_ROUTE_ENGLISH_MODEL = '/api/model/english'
    REMOTE_ROUTE_VOCABULARY_DATA = '/api/data/vocabulary'
    REMOTE_ROUTE_DYNAMIC_PINYIN_BLOCK = '/api/data/dpinyinblist'

    regex_all_english_word = re.compile("^[a-zA-Z\s\r\n]+$")
    regex_has_gap = re.compile("[a-zA-Z]+\s+[a-zA-Z]+")


    def __init__(self):

        self.service_data = settings.TWICE_SERVICE['default']
        self.service_addr = self.service_data['HOST']
        self.service_web_port = int(self.service_data['WEB_PORT'])
        self.service_tcpsocket_port = int(self.service_data['TCPSOCKET_PORT'])

        print('service_data: ', self.service_data)

        logging.info('=============  Remote Main Service Activated. Time Zone: [ {} ] ============='.format(settings.TIME_ZONE))


    def request_web(self, method = 'GET', uri = '/', dataset = {}):
        # print('start request_web: uri: ', uri, ' dataset: ', dataset)
        _conn = HTTPConnection(self.service_addr, self.service_web_port)
        body = None
        try:
            # _param = {}
            _params = urllib.parse.urlencode(dataset)
            # for idx, key in enumerate(dataset):
            #     _param[key] = json.dumps(dataset[key])
            _conn.request(method, uri, _params, 
                {"Content-type": "application/x-www-form-urlencoded"}
            )
            res = _conn.getresponse()
            if res.status == 200:

                body = res.read().decode()
                print('request_web get response body: ', body)
            
            else:

                print('res.status: ', res.status)
                body = res.read()
                print('[request_web] failed. ', body)
            
        except Exception as err:

            logging.error(str(err))
        
        return body


    def add_textbook_sentense(self, **args):
        return self.request_web(method='POST', uri='/api/twice/add_textbook_sentense', dataset=args)
    

    def saveRecord(self, prediction, message, text='', reason=''):
        try:

            pass

        except Exception as ex:

            logging.error('Save Record Failed,  message :: {}'.format(message))

        return None
            
    
