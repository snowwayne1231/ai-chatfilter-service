from dis import findlinestarts
from django.utils import timezone
from django.conf import settings
from django.forms.models import model_to_dict
# from django.core.files.base import ContentFile
from http.client import HTTPConnection
from ai.apps import MainAiApp
from ai.service_impact import get_all_vocabulary_from_models
from ai.helper import get_pinyin_path, get_grammar_path, get_english_model_path, get_pinyin_re_path, get_vocabulary_dictionary_path
from ai.classes.translator_pinyin import translate_by_string
from ai.models import TextbookSentense
from ai.train import train_pinyin_by_list, get_row_list_by_json_path
from dataparser.apps import MessageParser, EnglishParser
from dataparser.classes.store import ListPickle
from tensorflow.keras.callbacks import Callback

import numpy as np
import time, re, logging, json, threading
from os import path, listdir

from .classes.prefilter import PreFilter
# from .classes.fuzzycenter import FuzzyCenter
from .classes.chatstore import ChatStore
from .models import GoodSentence, BlockedSentence, AnalyzingData, UnknownWord, ChangeNicknameRequest, Blockword, DynamicPinyinBlock





class MainService():
    """

    """
    pre_filter = None
    ai_app = None
    message_parser = None
    english_parser = None
    fuzzy_center = None
    chat_store = None
    main_admin_server_addr = None
    is_open_mind = False
    is_admin_server = False

    timestamp_ymdh = [0, 0, 0, 0]
    service_avoid_filter_lv = 5
    lang_mode = 1
    vocabulary_data = {}
    is_training = False
    train_thread = None

    
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
    
    PATH_TEXTBOOK_JSON = '/assets/textbook/json/2022-02-17.json'
    # PATH_TEXTBOOK_JSON = '/assets/textbook/json/test.json'

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
            self.pre_filter.set_pinyin_block_list(self.get_dynamic_pinyin_block_list())

        logging.info('=============  Main Service Activated. Time Zone: [ {} ] ============='.format(settings.TIME_ZONE))


    def init_language(self):
        _setting = settings.LANGUAGE_MODE
        logging.info('Service Main Language [ {} ]'.format(_setting))
        if _setting == 'EN':
            self.lang_mode = self.STATUS_MODE_ENGLISH
        elif _setting == 'CH' or _setting == 'ZH':
            self.lang_mode = self.STATUS_MODE_CHINESE
        elif _setting == 'BERT':
            self.lang_mode = self.STATUS_MODE_BERT
        else:
            raise Exception('No Specify Right Language')


    def open_mind(self):
        if self.is_open_mind:
            return True



        _voca_data = self.get_vocabulary_data()
        _voca_pinyin = _voca_data.get('pinyin', [])

        _vocabulary_english = _voca_data.get('english', [])
        _vocabulary_chinese = _voca_data.get('chinese', [])
        _unknowns = _voca_data.get('unknowns', [])
        # _unknown_words = [_[0] for _ in _unknowns]

        self.english_parser.set_vocabulary(_vocabulary_english)

        # self.ai_app = MainAiApp(pinyin_data=_voca_pinyin, english_data=_vocabulary_english)
        _vocabulary_single_chinese = [_ for _ in _vocabulary_chinese if len(_[0])==1]
        self.ai_app = MainAiApp(pinyin_data=_voca_pinyin, english_data=_vocabulary_english, chinese_data=_vocabulary_single_chinese)
        
        if self.lang_mode == self.STATUS_MODE_CHINESE:
            #
            self.ai_app.load_chinese()

            is_version_of_reverse = int(settings.PINYIN_REVERSE) == 1
            self.ai_app.load_pinyin(is_version_of_reverse=is_version_of_reverse)

            self.ai_app.load_garmmar()

            self.ai_app.pinyin_model.save(is_check=True, is_continue=False)

        elif self.lang_mode == self.STATUS_MODE_ENGLISH:
            #
            self.ai_app.load_english()

        elif self.lang_mode == self.STATUS_MODE_BERT:
            
            self.ai_app.load_bert()

        else:

            logging.error('Language Mode Not Found :: {}'.format(self.lang_mode))
        

        self.is_open_mind = True
        # self.fuzzy_center = FuzzyCenter()

        return True
    

    def parse_message(self, string):
        _, lv, ac = self.message_parser.parse(string)
        # _ = self.english_parser.replace_to_origin_english(_)
        return _, lv, ac


    def trim_text(self, text):
        return self.message_parser.trim_only_general_and_chinese(text).strip()


    def think(self, message, user = '', room = '', silence=False, detail=False):
        st_time = time.time()
        if not self.is_open_mind:
            logging.warning('AI Is Not Ready..')
            return self.return_reslut(0, message=message, st_time=st_time)
        
        text = ''
        lv = 0
        anchor = 0
        reason_char = ''
        prediction = 0
        # print('receive message :', message)
        if message:
            text, lv, anchor = self.parse_message(message)
            # print('parse_message text: ', text)

        if lv >= self.service_avoid_filter_lv:
            return self.return_reslut(prediction, message=message, user=user, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)
        
        if user[:3] == 'TST':
            if anchor > 0 or room == 'BG01':
                return self.return_reslut(prediction, message=message, user=user, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

        if text:

            # check if mix some unknown message
            reason_char = self.find_prefilter_reject_reason_with_nonparsed_msg(text)
            if reason_char:
                prediction = self.STATUS_PREDICTION_NOT_ALLOW
                return self.return_reslut(prediction, message=message, user=user, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

            # parse to general text
            trimed_text = self.trim_text(text)
            if len(trimed_text) == 0 :
                return self.return_reslut(prediction, message=message, user=user, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)


            # print('text: [{}]   lv: [{}]   anchor: [{}]'.format(text, lv, anchor))

            # different language switch
            if self.lang_mode == self.STATUS_MODE_CHINESE:

                prediction, reason_char = self.prefilter_chinese(text)

            elif self.lang_mode == self.STATUS_MODE_ENGLISH:

                pass


            if reason_char:
                return self.return_reslut(prediction, message=message, user=user, room=room, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)
            
            # check same room conversation
            # room_texts = self.chat_store.get_texts_by_room(room)
            # reason_char = self.pre_filter.check_same_room_conversation(text, room_texts)
            reason_char = self.chat_store.check_same_room_conversation(trimed_text, room)
            if reason_char:
                prediction = self.STATUS_PREDICTION_SUSPECT_WATER_ARMY
                return self.return_reslut(prediction, message=message, user=user, room=room, text=trimed_text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

            if self.pre_filter.check_loginname_shorttime_saying(user):
                reason_char = 'Speak Too Quickly'
                prediction = self.STATUS_PREDICTION_SAME_LOGINNAME_IN_SHORTTIME
                return self.return_reslut(prediction, message=message, user=user, room=room, text=trimed_text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

            #main ai
            prediction, reason_char = self.ai_app.predict(trimed_text, lv=lv, with_reason=self.is_admin_server)
            
            # save message to room store
            if prediction == 0:
                self.store_temporary_text(
                    text=trimed_text,
                    user=user,
                    room=room,
                )

            return self.return_reslut(prediction, message=message, user=user, room=room, text=trimed_text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)

        else:

            prediction = self.STATUS_PREDICTION_NO_MSG

        return self.return_reslut(prediction, message=message, user=user, room=room, reason=reason_char, silence=silence, st_time=st_time)



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
            _trimed_engtxt = self.english_parser.trim(text).replace(' ', '').lower()
            _len_eng = len(_trimed_engtxt)
            # print('_trimed_engtxt: ', _trimed_engtxt)
            if 0 < _len_eng <= 2 and not self.english_parser.is_vocabulary(_trimed_engtxt):
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
        if result['spend_time'] > 0.2:
            logging.error('Spend Time Of Think Result = {}'.format(result['spend_time']))
        logging.debug('Think Result [ msg: {} prediction: {} time: {} ] '.format(result['message'], result['prediction'], result['spend_time']))
        return result


    def find_prefilter_reject_reason_with_nonparsed_msg(self, msg):
        # print('find_prefilter_reject_reason_with_nonparsed_msg: ', msg)
        methods = [
            self.pre_filter.find_suspect_digits_symbol,
            self.pre_filter.find_not_allowed_chat,
            self.pre_filter.find_korea_mixed,
            self.pre_filter.find_emoji_word_mixed,
            self.pre_filter.find_unallow_eng,
            self.pre_filter.find_pinyin_blocked,
        ]
        for m in methods:
            r = m(msg)
            if r:
                return r

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


    def get_dynamic_pinyin_block_list(self):
        return list(DynamicPinyinBlock.objects.values_list('id', 'text', 'pinyin').order_by('-id').all())
            
    

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

    
    def get_dynamic_pinyin_block_list_remotely(self, http_connection):
        http_connection.request('GET', self.REMOTE_ROUTE_DYNAMIC_PINYIN_BLOCK, headers={'Content-type': 'application/json'})
        _http_res = http_connection.getresponse()
        json_data = None
        if _http_res.status == 200:

            json_data = json.loads(_http_res.read().decode(encoding='utf-8'))
            logging.info('[get_dynamic_pinyin_block_list_remotely] Download Data Done.')
        else:
            logging.error('[get_dynamic_pinyin_block_list_remotely] Download Failed.')
        
        return json_data

    
    def get_textbook_sentense_list(self, latest = True):
        result = []
        _model = TextbookSentense.objects.values_list('id', 'origin', 'text', 'status', 'weight').order_by('-id')
        if latest:
            _first = TextbookSentense.objects.order_by('-id').first()
            if _first:
                _latest_origin = model_to_dict(_first, ['origin'])['origin']
                print('_latest_origin: ', _latest_origin)
                result = list(_model.filter(origin=_latest_origin))
        else:
            result = list(_model.all())
            
        return result


    def get_pinyin_model_path(self):
        self.open_mind()
        return self.ai_app.pinyin_model.get_model_path() if self.ai_app.pinyin_model else None


    def get_grammar_model_path(self):
        self.open_mind()
        return self.ai_app.grammar_model.get_model_path() if self.ai_app.grammar_model else None

    
    def get_english_model_path(self):
        self.open_mind()
        return self.ai_app.english_model.get_model_path() if self.ai_app.english_model else None

    
    def get_ai_train_data(self):
        _app = self.ai_app
        if _app:
            return _app.get_train_data()
        return {}


    def fetch_ai_model_data(self, remote_ip, port = 80):
        if self.is_admin_server:
            logging.error('Admin Server Can Not Fetch Data From Anywhere.')
            return exit(2)

        _http_cnn = HTTPConnection(remote_ip, port)
        self.main_admin_server_addr = (remote_ip, port)

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
            self.reload_pinyin_block(_http_cnn)

            _http_cnn.request('GET', self.REMOTE_ROUTE_PINYIN_MODEL)
            _http_res = _http_cnn.getresponse()
            if _http_res.status == 200:

                _chinese_model_path = get_pinyin_re_path() if int(settings.PINYIN_REVERSE) == 1 else get_pinyin_path()
                _save_file_by_http_response(response=_http_res, path=_chinese_model_path+'/model.remote.h5')
                logging.info('[fetch_ai_model_data] Download Remote Pinyin Model Done.')

            else:

                logging.error('[fetch_ai_model_data] Download Remote Pinyin Model Failed.')

            _http_cnn.request('GET', self.REMOTE_ROUTE_GARMMAR_MODEL)
            _http_res = _http_cnn.getresponse()
            if _http_res.status == 200:

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
        

    def add_textbook_sentense(self, origin='', sentenses=[]):
        limit_tbs_size = 100
        try:
            _exist_texts = list(TextbookSentense.objects.filter(origin=origin).values_list('text', flat=True))
            tbs = []
            for _sen in sentenses:
                _text = _sen[0]
                _status = int(_sen[1])
                _weight = int(_sen[2]) if _sen[2] else 1
                _text, _lv, _a = self.parse_message(_text)
                if _text and _status >= 0 and _text not in _exist_texts:
                    _textbook = TextbookSentense(
                        origin=origin,
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
            raise Exception(err)


    def add_pinyin_block(self, text):
        _num_max = 255
        try:
            if isinstance(text, list):
                _dps = []
                for _ in text:
                    _py = translate_by_string(_)
                    _dps.append(DynamicPinyinBlock(text=_, pinyin=_py))
                DynamicPinyinBlock.objects.bulk_create(_dps, batch_size=100)
                _ids = list(DynamicPinyinBlock.objects.values_list('pk', flat=True)[_num_max:])
                if len(_ids) > 0:
                    DynamicPinyinBlock.objects.filter(id__in=_ids).delete()
                return [model_to_dict(_) for _ in _dps]
            else:
                _py = translate_by_string(text)
                qs = DynamicPinyinBlock.objects.filter(pinyin=_py)
                if len(qs) == 0:
                    qs = DynamicPinyinBlock.objects.create(
                        text=text,
                        pinyin=_py,
                    )
                    _count = DynamicPinyinBlock.objects.count()
                    if _count > _num_max:
                        DynamicPinyinBlock.objects.all().first().delete()
                    return model_to_dict(qs)
                else:
                    return None
        except Exception as err:
            print('add_pinyin_block error: ', err)
            return None


    def remove_textbook_sentense(self, id):
        try:
            if isinstance(id, int):
                TextbookSentense.objects.get(pk=id).delete()
            elif id == 'all':
                TextbookSentense.objects.all().delete()
            return True
        except Exception as err:
            return False


    def remove_pinyin_block(self, id):
        try:
            DynamicPinyinBlock.objects.get(pk=id).delete()
            return True
        except Exception as err:
            return False


    def reload_pinyin_block(self, conn = None):
        print('[Reload_pinyin_block] Triggered.')
        if conn:
            _dpb_list = self.get_dynamic_pinyin_block_list_remotely(conn)
        elif self.main_admin_server_addr:
            _ip, _port = self.main_admin_server_addr
            _dpb_list = self.get_dynamic_pinyin_block_list_remotely(HTTPConnection(_ip, _port))
        else:
            _dpb_list = self.get_dynamic_pinyin_block_list()
        
        self.pre_filter.set_pinyin_block_list(_dpb_list)


    def get_model_versions(self):
        result = {'pinyin': []}
        _pinyin_path = get_pinyin_path(is_version=True)
        result['pinyin'] = listdir(_pinyin_path)
        return result


    def fit_pinyin_model_autoly(self):
        if self.is_training:
            if self.train_thread:
                _is_on_training = self.train_thread.get_is_training()
                if _is_on_training:
                    print('Service is already in training...', flush=True)
                    return 'Service is already in training...'
                
                self.is_training = _is_on_training
            else:
                return 'Training Thread Not Setting.'
            
        _json_textbook_path = self.ai_app.get_ai_dir() + self.PATH_TEXTBOOK_JSON
        _max_spend_time = 20
        _final_accuracy = 0.9994
        result_list = get_row_list_by_json_path(_json_textbook_path)
        db_textbooks = TextbookSentense.objects.values_list('id', 'origin', 'text', 'status', 'weight').order_by('id')
        lasest_origin = ''
        
        if db_textbooks:
            lasest_origin = db_textbooks[0][1]
            _append_db_textbooks = [['', _[4], _[2], _[3]] for _ in db_textbooks]
            result_list.extend(_append_db_textbooks)

        if self.ai_app and self.ai_app.pinyin_model:
            self.train_thread = ThreadPinyinModel(args=(result_list, _final_accuracy, _max_spend_time, lasest_origin), model=self.ai_app.pinyin_model, model_simple=self.ai_app.chinese_model)
            self.is_training = True
            self.train_thread.start()
        else:
            return 'Pinyin model is Not ready.'
        
        return lasest_origin


    def thred_train_stop(self):
        if self.ai_app and self.ai_app.pinyin_model:
            self.ai_app.pinyin_model.save(is_check=True, is_continue=True, eta=-1)
        
        if self.is_training:
            if self.train_thread.is_alive():
                self.ai_app.pinyin_model.set_stop()
                self.train_thread.stop()
            # self.ai_app.pinyin_model.save(is_check=True, is_continue=False)
        
        return True


    def get_test_accuracy_by_origin(self, origin=''):
        result = {'acc': 0, 'length': 0, 'right': 0, 'wrongs': []}
        _list = TextbookSentense.objects.filter(origin=origin).values_list('text', 'status')
        _list = list(_list)
        result['length'] = len(_list)
        if result['length'] > 0:
            for _ in _list:
                _text = _[0]
                _status = _[1]
                _prediction = self.think(_text)['prediction']
                _is_delete = _prediction > 0
                _ans_delete = _status > 0
                if _is_delete == _ans_delete:
                    result['right'] += 1
                else:
                    result['wrongs'].append(_text)

            result['acc'] = result['right'] / result['length']

        return result
        




set_training_finishe = False

class ThreadTrainingCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        global set_training_finishe
        print('[ThreadTrainingCallback][on_epoch_end] training: ', set_training_finishe)
        if set_training_finishe:
            self.model.stop_training = True




class ThreadPinyinModel(threading.Thread):
    """
    """
    model = None
    model_simple = None
    history = None
    ontraning = False


    def __init__(self, target=None, args=(), model=None, model_simple=None):
        super(ThreadPinyinModel, self).__init__(args=args, target=target)
        self.args = args
        self.model = model
        self.model_simple = model_simple
        
    
    def thread_train_pinyin(self, train_data, stop_accuracy, stop_hours, origin):
        print('========== Thread_Train_Pinyin ========== ')
        print('train_data lengtn: ', len(train_data), flush=True)
        print('stop_accuracy: ', stop_accuracy, flush=True)
        print('stop_hours: ', stop_hours, flush=True)
        print('train_data [-5:]: ', train_data[-5:], flush=True)
        self.ontraning = True
        if self.model_simple:
            self.model_simple.save(is_check=True, history={'validation': 0.0}, is_continue=True, eta=1, origin=origin)
            _history_simple = self.model_simple.fit_model(train_data=train_data[-8000:], stop_accuracy=0.999, stop_hours=1, origin=origin, verbose=0)

        self.model.save(is_check=True, history={'validation': 0.0}, is_continue=True, eta=stop_hours, origin=origin)
        self.history = self.model.fit_model(train_data=train_data[-120000:] if len(train_data) > 150000 else train_data, stop_accuracy=stop_accuracy, stop_hours=stop_hours, origin=origin, verbose=0, callback=ThreadTrainingCallback())
        
        self.ontraning = False
        return False


    def get_history(self):
        return self.history


    def get_is_training(self):
        return self.ontraning


    def stop(self):
        self.model.set_stop()
        global set_training_finishe
        set_training_finishe = True

    
    def run(self):
        global set_training_finishe
        try:
            set_training_finishe = False
            train_data = self.args[0]
            stop_accuracy = self.args[1]
            stop_hours = self.args[2]
            origin = self.args[3]
            self.thread_train_pinyin(train_data, stop_accuracy, stop_hours, origin)

        except Exception as err:

            print(err, flush=True)
        
        finally:

            self.model.save(is_check=True, is_continue=False, origin=origin)
            self.ontraning = False
            
