from django.utils import timezone
from django.conf import settings
from ai.apps import MainAiApp
from dataparser.apps import MessageParser
from .classes.prefilter import PreFilter
# from .classes.fuzzycenter import FuzzyCenter
from .classes.chatstore import ChatStore
from .models import GoodSentence, BlockedSentence, AnalyzingData, UnknownWord, Textbook
import numpy as np
import time, re
from service.widgets import printt
from ai.apps import pinyin_model_path, grammar_model_path
from django.core.files.base import ContentFile



class MainService():
    """

    """
    pre_filter = None
    ai_app = None
    message_parser = None
    fuzzy_center = None
    chat_store = None
    is_open_mind = False
    is_admin_server = False

    timestamp_ymdh = [0, 0, 0, 0]
    service_avoid_filter_lv = 6
    service_avoid_ai_lv = 15

    
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

    regex_all_english_word = re.compile("^[a-zA-Z\s\r\n]+$")


    def __init__(self, is_admin_server = False):

        self.message_parser = MessageParser()
        self.chat_store = ChatStore()
        if is_admin_server:
            self.is_admin_server = True
            self.check_analyzing()
        print('=============  Main Service Activated. Time Zone: [ {} ] ============='.format(settings.TIME_ZONE))


    def open_mind(self, pinyin_data=None):
        if self.is_open_mind:
            return True

        self.pre_filter = PreFilter()
        
        if pinyin_data:
            _vocabulary = pinyin_data.get('vocabulary', [])
            _unknowns = pinyin_data.get('unknowns', [])
            _unknown_words = [_[0] for _ in _unknowns]
            self.ai_app = MainAiApp(jieba_vocabulary=_vocabulary, pinyin_unknown_words=_unknown_words)

            
        elif self.is_admin_server:

            self.ai_app = MainAiApp()
            _vocabulary = self.ai_app.get_pinyin_vocabulary()
        
        else:
            printt('Open Mind Failed. It is Not Admin Server.')
            return False
        
        _single_words = [_ for _ in _vocabulary if _.count('_') == 1]
        self.pre_filter.set_single_words(_single_words)

        self.is_open_mind = True
        # self.fuzzy_center = FuzzyCenter()

        return True
    

    def parse_message(self, string):
        return self.message_parser.parse(string)


    def think(self, message, user = '', room = '', silence=False, detail=False):
        st_time = time.time()
        if not self.is_open_mind:
            print('AI Is Not Ready..')
            return self.return_reslut(0, message=message, st_time=st_time)
        
        text = ''
        reason_char = ''
        # print('receive message :', message)

        if message:
            
            reason_char = self.pre_filter.find_special_char(message)

            if reason_char:
                prediction = self.STATUS_PREDICTION_SPECIAL_CHAR
                return self.return_reslut(prediction, message=message, reason=reason_char, silence=silence, st_time=st_time)
            # elif not detail:   # temporary to use 
            #     return self.return_reslut(0, message=message)


            text, lv, anchor = self.parse_message(message)

            if anchor > 0:
                return self.return_reslut(0, message=message, text=text, silence=silence, st_time=st_time)

            if len(text) == 0:
                return self.return_reslut(0, message=message, text=text, silence=silence, st_time=st_time)

            if len(text) == 0:
                return self.return_reslut(0, message=message, text=text, silence=silence, st_time=st_time)

            _is_all_english_word = self.regex_all_english_word.match(text)
            if _is_all_english_word and len(text) > 7:
                print('[INFO] All English Allow Pass: [{}].'.format(text))
                return self.return_reslut(0, message=message, text=text, silence=silence, st_time=st_time)
            
            
            if lv < self.service_avoid_filter_lv:

                reason_char = self.pre_filter.find_wechat_char(text)
                if reason_char:

                    prediction = self.STATUS_PREDICTION_WEHCAT_SUSPICION
                    return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence, st_time=st_time)

                
                # reason_char = self.fuzzy_center.find_fuzzy_block_word(text, silence=silence)
                # if reason_char:

                #     prediction = self.STATUS_PREDICTION_BLOCK_WORD
                #     return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence, st_time=st_time)


                room_texts = self.chat_store.get_texts_by_room(room)
                reason_char = self.pre_filter.check_same_room_conversation(text, room_texts)
                if reason_char:
                    prediction = self.STATUS_PREDICTION_SUSPECT_WATER_ARMY
                    # print('deleted by SUSPECT_WATER_ARMY: ', text)
                    return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence, st_time=st_time)


            #main ai
            if lv < self.service_avoid_ai_lv:
                prediction, reason_char = self.ai_app.predict(text, lv=lv, with_reason=self.is_admin_server)

            if prediction == 0:
                self.store_temporary_text(
                    text=text,
                    user=user,
                    room=room,
                )

            return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence, detail=detail, st_time=st_time)
                
        else:

            prediction = self.STATUS_PREDICTION_NO_MSG

        return self.return_reslut(prediction, message=message, reason=reason_char, silence=silence, st_time=st_time)



    def return_reslut(self, prediction, message, user='', room='', text='', reason='', silence=True, detail=False, st_time=0):
        result = {}
        detail_data = {}
        # if not silence:

        #     self.saveRecord(prediction, message=message, text=text, reason=reason)
        #     self.check_analyzing()
        
        if detail:

            detail_data = self.ai_app.get_details(text)
            # print('prediction: ', prediction)
            # print('message: ', message)
            # print('text: ', text)
            # print('reason: ', reason)
            # print('detail_data: ', detail_data)

        ed_time = time.time()
        
        result['user'] = user
        result['room'] = room
        result['message'] = message
        result['text'] = text
        result['prediction'] = int(prediction)
        result['reason_char'] = reason
        result['detail'] = detail_data
        result['spend_time'] = ed_time - st_time

        return result

    
    def store_temporary_text(self, text, user, room):
        self.chat_store.upsert_text(text, user, room)


    def saveRecord(self, prediction, message, text='', reason=''):
        if self.is_admin_server:
            if prediction == 0:
                # save to good sentence
                record = GoodSentence(
                    message=message[:95],
                    text=text[:63],
                )
            else:
                # save to blocked
                if text:
                    _text, lv, anchor = self.parse_message(message)
                else:
                    _text = ''
                
                record = BlockedSentence(
                    message=message[:95],
                    text=_text[:63],
                    reason=reason[:63] if reason else '',
                    status=int(prediction),
                )

            record.save()
        
            self.check_analyzing()

        else:

            print('Save Record Failed, Is Not Admin Server.')


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


    def get_pinyin_data(self):
        if self.ai_app:
            return {
                'vocabulary': self.ai_app.get_pinyin_vocabulary(),
                'unknowns': self.get_pinyin_unknowns(),
            }
        else:
            return {}

    def get_pinyin_unknowns(self):
        if self.is_admin_server:
            _unknowns = [[_, ''] for _ in UnknownWord.objects.values_list('unknown', flat=True)]
        else:
            _unknowns = self.ai_app.get_pinyin_unknowns()


        return _unknowns

    def get_train_textbook(self):
        _limit = 5000
        queryset = Textbook.objects.filter(type=1).values_list('text', 'model', 'status').order_by('-id')[:_limit]
        result = list(queryset)
        # print('get_train_textbook: ', result)
        return result


    def fit_pinyin_model(self, datalist):
        _hours = 2
        print('=== fit_pinyin_model ===', _hours)
        self.ai_app.pinyin_model.fit_model(train_data=datalist, stop_hours=_hours)
        print('=== fit_pinyin_model end ===')

