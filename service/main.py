from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from http.client import HTTPConnection
from ai.apps import MainAiApp
from ai.service_impact import get_all_vocabulary_from_models
from ai.helper import get_pinyin_path, get_grammar_path, get_english_model_path, get_vocabulary_dictionary_path
from dataparser.apps import MessageParser, EnglishParser
from dataparser.classes.store import ListPickle

import numpy as np
import time, re, logging, json
from os import path, listdir

from .classes.prefilter import PreFilter
# from .classes.fuzzycenter import FuzzyCenter
from .classes.chatstore import ChatStore
from .models import GoodSentence, BlockedSentence, AnalyzingData, UnknownWord, ChangeNicknameRequest
from ai.models import TextbookSentense




class MainService():
    """

    """
    pre_filter = None
    ai_app = None
    message_parser = None
    english_parser = None
    fuzzy_center = None
    chat_store = None
    is_open_mind = False
    is_admin_server = False

    timestamp_ymdh = [0, 0, 0, 0]
    service_avoid_filter_lv = 5
    lang_mode = 1
    vocabulary_data = {}

    
    STATUS_PREDICTION_NO_MSG = 0
    STATUS_PREDICTION_ADVERTISING = 1
    STATUS_PREDICTION_HUMAN_DELETE = 3
    STATUS_PREDICTION_DIRTY_WORD = 4
    STATUS_PREDICTION_OTHER_AI = 5
    STATUS_PREDICTION_SPECIAL_CHAR = 11
    STATUS_PREDICTION_NONSENSE = 12
    STATUS_PREDICTION_WEHCAT_SUSPICION = 13
    STATUS_PREDICTION_BLOCK_WORD = 14
    STATUS_PREDICTION_SUSPECT_WATER_ARMY = 15
    STATUS_PREDICTION_NOT_ALLOW = 16

    STATUS_MODE_CHINESE = 1
    STATUS_MODE_ENGLISH = 2

    REMOTE_ROUTE_PINYIN_MODEL = '/api/model/pinyin'
    REMOTE_ROUTE_GARMMAR_MODEL = '/api/model/grammar'
    REMOTE_ROUTE_ENGLISH_MODEL = '/api/model/english'
    REMOTE_ROUTE_VOCABULARY_DATA = '/api/data/vocabulary'

    regex_all_english_word = re.compile("^[a-zA-Z\s\r\n]+$")
    regex_has_gap = re.compile("[a-zA-Z]+\s+[a-zA-Z]+")


    def __init__(self, is_admin_server = False):

        self.init_language()
        self.message_parser = MessageParser()
        self.english_parser = EnglishParser()
        self.chat_store = ChatStore()
        self.pre_filter = PreFilter()

        if is_admin_server:
            self.is_admin_server = True
            self.check_analyzing()

        logging.info('=============  Main Service Activated. Time Zone: [ {} ] ============='.format(settings.TIME_ZONE))


    def init_language(self):
        _setting = settings.LANGUAGE_MODE
        if _setting == 'EN':
            self.lang_mode = self.STATUS_MODE_ENGLISH
        else:
            self.lang_mode = self.STATUS_MODE_CHINESE

        logging.info('Service Main Language [{}]'.format(_setting))


    def open_mind(self):
        if self.is_open_mind:
            return True



        _voca_data = self.get_vocabulary_data()
        _voca_pinyin = _voca_data.get('pinyin', [])

        _vocabulary_english = _voca_data.get('english', [])
        _unknowns = _voca_data.get('unknowns', [])
        # _unknown_words = [_[0] for _ in _unknowns]

        self.english_parser.set_vocabulary(_vocabulary_english)

        self.ai_app = MainAiApp(pinyin_data=_voca_pinyin, english_data=_vocabulary_english)
        


        if self.lang_mode == self.STATUS_MODE_CHINESE:
            #
            self.ai_app.load_pinyin()

            self.ai_app.load_garmmar()

        elif self.lang_mode == self.STATUS_MODE_ENGLISH:
            #
            self.ai_app.load_english()

        else:

            logging.error('Language Mode Not Found :: {}'.format(self.lang_mode))
        

        self.is_open_mind = True
        # self.fuzzy_center = FuzzyCenter()

        return True
    

    def parse_message(self, string):
        _, lv, ac = self.message_parser.parse(string)
        # _ = self.english_parser.replace_to_origin_english(_)
        return _, lv, ac


    def think(self, message, user = '', room = '', silence=False, detail=False):
        st_time = time.time()
        if not self.is_open_mind:
            logging.warning('AI Is Not Ready..')
            return self.return_reslut(0, message=message, st_time=st_time)
        
        text = ''
        reason_char = ''
        prediction = 0
        # print('receive message :', message)

        if message:

            # check if mix some unknown message
            reason_char = self.find_prefilter_reject_reason_with_nonparsed_msg(message)
            if reason_char:
                prediction = self.STATUS_PREDICTION_NOT_ALLOW
                return self.return_reslut(prediction, message=message, room=room, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

            # parse
            text, lv, anchor = self.parse_message(message)

            # is not general player
            if anchor > 0 or len(text) == 0 or lv >= self.service_avoid_filter_lv:
                return self.return_reslut(prediction, message=message, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)


            # print('text: [{}]   lv: [{}]   anchor: [{}]'.format(text, lv, anchor))

            # different language switch
            if self.lang_mode == self.STATUS_MODE_CHINESE:

                prediction, reason_char = self.prefilter_chinese(text)

            elif self.lang_mode == self.STATUS_MODE_ENGLISH:

                pass


            if reason_char:
                return self.return_reslut(prediction, message=message, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)
            
            # check same room conversation
            room_texts = self.chat_store.get_texts_by_room(room)
            reason_char = self.pre_filter.check_same_room_conversation(text, room_texts)
            if reason_char:
                prediction = self.STATUS_PREDICTION_SUSPECT_WATER_ARMY
                return self.return_reslut(prediction, message=message, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

            #main ai
            prediction, reason_char = self.ai_app.predict(text, lv=lv, with_reason=self.is_admin_server)
            
            # save message to room store
            if prediction == 0:
                self.store_temporary_text(
                    text=text,
                    user=user,
                    room=room,
                )

            return self.return_reslut(prediction, message=message, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)
                
        else:

            prediction = self.STATUS_PREDICTION_NO_MSG

        return self.return_reslut(prediction, message=message, room=room, reason=reason_char, silence=silence, st_time=st_time)



    def prefilter_chinese(self, text):

        reason_char = self.pre_filter.find_wechat_char(text)
        if reason_char:
            return self.STATUS_PREDICTION_WEHCAT_SUSPICION, reason_char

        
        _is_all_english_word = self.regex_all_english_word.match(text)

        if _is_all_english_word:

            if self.regex_has_gap.match(text) and len(text.replace(' ', '')) > 12:

                text = self.english_parser.replace_to_origin_english(text)

            _is_allowed = self.is_allowed_english_sentense(text)
            if _is_allowed:
                reason_char = 'Allowed English'
                logging.debug('[INFO] All Right English Allow Pass : [{}].'.format(text))
                return 0, reason_char
        
        else:
            # wechat suspected english style
            _trimed_engtxt = self.english_parser.trim(text).replace(' ', '')
            _len_eng = len(_trimed_engtxt)
            if 0 < _len_eng <= 2 and not self.english_parser.is_vocabulary(_len_eng):
                _len = len(text)
                if  _len > 4:
                    return self.STATUS_PREDICTION_WEHCAT_SUSPICION, 'Wechat Suspected'
        
        return 0, reason_char


    def return_reslut(self, prediction, message, user='', room='', text='', reason='', silence=True, detail=False, st_time=0):
        result = {}
        detail_data = {}
        
        if detail:

            detail_data = self.ai_app.get_details(text)

        ed_time = time.time()
        
        result['user'] = user
        result['room'] = room
        result['message'] = message
        result['text'] = text
        result['prediction'] = int(prediction)
        result['reason_char'] = reason
        result['detail'] = detail_data
        result['spend_time'] = ed_time - st_time
        # print('Spend Time = ', result['spend_time'])
        return result


    def find_prefilter_reject_reason_with_nonparsed_msg(self, msg):
        # print('find_prefilter_reject_reason_with_nonparsed_msg: ', msg)
        reason_char = self.pre_filter.find_not_allowed_chat(msg)
        if reason_char:
            return reason_char
        reason_char = self.pre_filter.find_korea_mixed(msg)
        if reason_char:
            return reason_char
        reason_char = self.pre_filter.find_emoji_word_mixed(msg)
        if reason_char:
            return reason_char
        reason_char = self.pre_filter.find_unallow_eng(msg)
        if reason_char:
            return reason_char

        return False
    

    def store_temporary_text(self, text, user, room):
        self.chat_store.upsert_text(text, user, room)


    def saveRecord(self, prediction, message, text='', reason=''):
        try:

            if prediction == 0:
                # save to good sentence
                record = GoodSentence(
                    message=message[:95],
                    text=text[:63],
                )
            else:
                # save to blocked
                if text:
                    _text = text
                else:
                    _text, lv, anchor = self.parse_message(message)
                
                record = BlockedSentence(
                    message=message[:95],
                    text=_text[:63],
                    reason=reason[:63] if reason else '',
                    status=int(prediction),
                )

            record.save()
        
            self.check_analyzing()

        except Exception as ex:

            logging.error('Save Record Failed,  message :: {}'.format(message))
            print(ex, flush=True)

    
    def saveNicknameRequestRecord(self, nickname, status):
        if self.is_admin_server:

            try:
                record = ChangeNicknameRequest(
                    nickname=nickname,
                    status=status,
                )
                record.save()
            except Exception as ex:
                logging.error('Save NicknameRequestRecord Failed, nickname: [{}].'.format(nickname))
                print(ex)



    def check_analyzing(self):
        _now = timezone.now()
        today_datetime = timezone.localtime(_now)
        _ymdh = [_now.year, _now.month, _now.day, _now.hour]
        _not_day_matched = _ymdh[2] != self.timestamp_ymdh[2]
        _not_hour_matched = _ymdh[3] != self.timestamp_ymdh[3]


        if _not_day_matched:
            today_date = today_datetime.replace(hour=0,minute=0,second=0)
            yesterday_date = today_date + timezone.timedelta(days=-1)
            yesterday_goods = GoodSentence.objects.filter(date__gte=yesterday_date, date__lte=today_date).count()
            yesterday_blockeds = BlockedSentence.objects.filter(date__gte=yesterday_date, date__lte=today_date).count()

            yesterday_analyzing = AnalyzingData.objects.filter(
                year=yesterday_date.year,
                month=yesterday_date.month,
                day=yesterday_date.day,
            )

            if yesterday_analyzing:

                yesterday_analyzing.update(
                    good_sentence=yesterday_goods,
                    blocked_sentence=yesterday_blockeds,
                )

            else:

                yesterday_analyzing = AnalyzingData(
                    year=yesterday_date.year,
                    month=yesterday_date.month,
                    day=yesterday_date.day,
                    good_sentence=yesterday_goods,
                    blocked_sentence=yesterday_blockeds,
                )

                yesterday_analyzing.save()

            self.timestamp_ymdh[2] = _now.day

        if _not_hour_matched:
            today_date = today_datetime.replace(hour=0,minute=0,second=0)
            today_goods = GoodSentence.objects.filter(date__gte=today_date).count()
            today_blockeds = BlockedSentence.objects.filter(date__gte=today_date).count()
            today_analyzing = AnalyzingData.objects.filter(
                year=today_date.year,
                month=today_date.month,
                day=today_date.day,
            )

            if today_analyzing:

                today_analyzing.update(
                    good_sentence=today_goods,
                    blocked_sentence=today_blockeds,
                )

            else:
                today_analyzing = AnalyzingData(
                    year=today_date.year,
                    month=today_date.month,
                    day=today_date.day,
                    good_sentence=today_goods,
                    blocked_sentence=today_blockeds,
                )

                today_analyzing.save()
                
            self.timestamp_ymdh = _ymdh


    def is_allowed_english_sentense(self, text):
        
        _parsed_english_list = self.english_parser.parse_right_vocabulary_list(text)
        _length_eng = len(_parsed_english_list)

        if _parsed_english_list:
            
            if _length_eng == 1:
                _single_word = _parsed_english_list[0]
                _num_eng_word = len(_single_word)
                # print('[is_allowed_english_sentense] _single_word: ', _single_word)
                return _num_eng_word < 3
                # _is_origin_english_word = _num_eng_word == len(text)
                # return _is_origin_english_word or _num_eng_word > 9
                # print('_is_origin_english_word: text = {}, _single_word = {}'.format(text, _single_word) )
                # return _is_origin_english_word
            
            if len(''.join(_parsed_english_list)) < 15:
                return False
            
            _english_map = {}
            for _eng in _parsed_english_list:
                if _eng in _english_map:
                    _english_map[_eng] += 1
                else:
                    _english_map[_eng] = 1

            _total = 0
            _double_eng = 0
            for _num_eng in _english_map.values():
                _total += 1
                if _num_eng > 1:
                    _double_eng += 1

            _double_rate = _double_eng / _total
            if _double_rate < 0.25 and _length_eng > 3:
                return True

        return False


    def get_english_parser(self):
        return self.english_parser
    

    def get_vocabulary_data(self):
        if self.vocabulary_data:
            return self.vocabulary_data
        elif self.is_admin_server:
            
            _unknowns = [[_['unknown'], _['text']] for _ in UnknownWord.objects.values('unknown', 'text')]
            _voca = get_all_vocabulary_from_models()
            _voca['unknowns'] = _unknowns
            # self.vocabulary_data = _voca
            return _voca
        else:
            _data_pk = ListPickle(get_vocabulary_dictionary_path() + '/data.pickle')
            return _data_pk.get_list()[0] or {}
            
    

    def get_vocabulary_data_remotely(self, http_connection):
        
        http_connection.request('GET', self.REMOTE_ROUTE_VOCABULARY_DATA, headers={'Content-type': 'application/json'})
        _http_res = http_connection.getresponse()
        if _http_res.status == 200:

            _json_data = json.loads(_http_res.read().decode(encoding='utf-8'))
            logging.info('[get_vocabulary_data_remotely] Download Data Done.')

        else:

            _json_data = None
            logging.error('[get_vocabulary_data_remotely] Download Failed.')

        _data_pk = ListPickle(get_vocabulary_dictionary_path() + '/data.pickle')
        if _json_data:
            _data_pk.save([_json_data])
        else:
            # _json_data = _data_pk.get_list()[0]
            _json_data = {}
        
        return _json_data
    


    def get_pinyin_model_path(self):
        self.open_mind()
        return self.ai_app.pinyin_model.get_model_path() if self.ai_app.pinyin_model else None


    def get_grammar_model_path(self):
        self.open_mind()
        return self.ai_app.grammar_model.get_model_path() if self.ai_app.grammar_model else None

    
    def get_english_model_path(self):
        self.open_mind()
        return self.ai_app.english_model.get_model_path() if self.ai_app.english_model else None


    def fetch_ai_model_data(self, remote_ip, port = 80):
        if self.is_admin_server:
            logging.error('Admin Server Can Not Fetch Data From Anywhere.')
            return exit(2)

        _http_cnn = HTTPConnection(remote_ip, port)

        def _save_file_by_http_response(response, path):
            with open(path, 'wb+') as f:
                while True:
                    _buf = response.read()
                    if _buf:
                        f.write(_buf)
                    else:
                        break

        self.vocabulary_data = self.get_vocabulary_data_remotely(_http_cnn)

        if self.lang_mode == self.STATUS_MODE_CHINESE:
            #
            _http_cnn.request('GET', self.REMOTE_ROUTE_PINYIN_MODEL)
            _http_res = _http_cnn.getresponse()
            if _http_res.status == 200:

                # _save_file_by_http_response(response=_http_res, path=get_pinyin_path()+'/model.h5')
                _save_file_by_http_response(response=_http_res, path=get_pinyin_path()+'/model.remote.h5')
                logging.info('[fetch_ai_model_data] Download Remote Pinyin Model Done.')

            else:

                logging.error('[fetch_ai_model_data] Download Remote Pinyin Model Failed.')

            _http_cnn.request('GET', self.REMOTE_ROUTE_GARMMAR_MODEL)
            _http_res = _http_cnn.getresponse()
            if _http_res.status == 200:

                # _save_file_by_http_response(response=_http_res, path=get_grammar_path()+'/model.h5')
                _save_file_by_http_response(response=_http_res, path=get_grammar_path()+'/model.remote.h5')
                logging.info('[fetch_ai_model_data] Download Remote Grammar Model Done.')

            else:

                logging.error('[fetch_ai_model_data] Download Remote Grammar Model Failed.')


        elif self.lang_mode == self.STATUS_MODE_ENGLISH:
            #
            _http_cnn.request('GET', self.REMOTE_ROUTE_ENGLISH_MODEL)
            _http_res = _http_cnn.getresponse()
            if _http_res.status == 200:

                # _save_file_by_http_response(response=_http_res, path=get_english_model_path()+'/model.h5')
                _save_file_by_http_response(response=_http_res, path=get_english_model_path()+'/model.remote.h5')
                logging.info('[fetch_ai_model_data] Download Remote English Model Done.')

            else:

                logging.error('[fetch_ai_model_data] Download Remote English Model Failed.')
        

    def add_textbook_sentense(self, sentenses):
        limit_tbs_size = 50
        try:
            tbs = []
            for _sen in sentenses:
                _origin_sen = _sen[0]
                _status = _sen[1]
                _weight = _sen[2] or 1
                _text, _lv, _a = self.parse_message(_origin_sen)
                if _text and _status:
                    _textbook = TextbookSentense(
                        origin=_origin_sen,
                        text=_text,
                        status=_status,
                        weight=_weight,
                    )
                    tbs.append(_textbook)
                # _textbook.save()
                if len(tbs) >= limit_tbs_size:
                    TextbookSentense.objects.bulk_create(tbs)
                    tbs = []

            if len(tbs) > 0:
                TextbookSentense.objects.bulk_create(tbs)

            return True
        except Exception as err:
            logging.error(str(err))
            return False


    def remove_textbook_sentense(self, id):
        try:
            TextbookSentense.objects.get(pk=id).delete()
            return True
        except Exception as err:
            return False

    
    def get_model_versions(self):
        result = {'pinyin': []}
        _pinyin_path = get_pinyin_path(is_version=True)
        result['pinyin'] = listdir(_pinyin_path)
        return result

        
    

        

        

        

