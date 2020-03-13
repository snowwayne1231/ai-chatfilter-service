from django.utils import timezone
from django.conf import settings
from ai.apps import MainAiApp
from dataparser.apps import MessageParser
from .classes.prefilter import PreFilter
from .classes.fuzzycenter import FuzzyCenter
from .models import GoodSentence, BlockedSentence, AnalyzingData
import numpy as np
import time




class MainService():
    pre_filter = None
    ai_app = None
    message_parser = None
    fuzzy_center = None
    timestamp_ymdh = [0, 0, 0, 0]
    STATUS_PREDICTION_ADVERTISING = 1
    STATUS_PREDICTION_HUMAN_DELETE = 3
    STATUS_PREDICTION_DIRTY_WORD = 4
    STATUS_PREDICTION_OTHER_AI = 5
    STATUS_PREDICTION_NO_MSG = 0
    STATUS_PREDICTION_SPECIAL_CHAR = 11
    STATUS_PREDICTION_NONSENSE = 12
    STATUS_PREDICTION_WEHCAT_SUSPICION = 13
    STATUS_PREDICTION_BLOCK_WORD = 14

    def __init__(self):
        print('Setting Time Zone: [ {} ]'.format(settings.TIME_ZONE))
        
        self.ai_app = MainAiApp()
        self.message_parser = MessageParser()

        
        self.pre_filter = PreFilter()
        self.fuzzy_center = FuzzyCenter()
        self.check_analyzing()
        print('=============  Main Service Activated.  =============')

    
    def parse_message(self, string):
        return self.message_parser.parse(string)


    def think(self, message, user = '', room = '', silence=False, detail=False):
        result = {}
        text = ''
        merged_text = ''
        reason_char = ''
        _st_time = time.time()
        print('receive message :', message)

        if message:
            
            reason_char = self.pre_filter.find_special_char(message)

            if reason_char:
                prediction = self.STATUS_PREDICTION_SPECIAL_CHAR
                return self.return_reslut(prediction, message=message, reason=reason_char, silence=silence)
            elif not detail:   # temporary to use 
                return self.return_reslut(0, message=message)


            text, lv, anchor = self.parse_message(message)

            if anchor > 0:
                return self.return_reslut(0, message=message, text=text, silence=silence)

            if len(text) == 0:
                return self.return_reslut(0, message=message, text=text, silence=silence)
            
            
            # merged_text = self.get_merged_text(text, user, room)
            merged_text = text


            reason_char = self.pre_filter.find_wechat_char(merged_text)
            if reason_char:

                prediction = self.STATUS_PREDICTION_WEHCAT_SUSPICION
                return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence)

                
            reason_char = self.fuzzy_center.find_fuzzy_block_word(merged_text, silence=silence)
            if reason_char:

                prediction = self.STATUS_PREDICTION_BLOCK_WORD
                return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence)


            prediction, reason_char = self.ai_app.predict(merged_text, lv=lv, silence=silence)

            self.store_temporary_text(
                text=text,
                user=user,
                room=room,
                lv=lv,
                anchor=anchor,
                prediction=prediction,
            )

            return self.return_reslut(prediction, message=message, text=text, reason=reason_char, silence=silence, detail=detail)
                
        else:

            prediction = self.STATUS_PREDICTION_NO_MSG

        return self.return_reslut(prediction, message=message, reason=reason_char, silence=silence)



    def return_reslut(self, prediction, message, user='', room='', text='', reason='', silence=True, detail=False):
        result = {}
        detail_data = {}
        if not silence:

            self.saveRecord(prediction, message=message, text=text, reason=reason)
            self.check_analyzing()
        
        if detail:

            detail_data = self.ai_app.get_details(text)
            print('prediction: ', prediction)
            print('message: ', message)
            print('text: ', text)
            print('reason: ', reason)
            print('detail_data: ', detail_data)
        
        result['user'] = user
        result['room'] = room
        result['message'] = message
        result['text'] = text
        result['prediction'] = prediction
        result['reason_char'] = reason
        result['detail'] = detail_data

        return result

    
    def store_temporary_text(self, text, user, room, lv, anchor, prediction):
        self.fuzzy_center.upsert_temp_text(text, user, room, lv, anchor, prediction)

    def get_merged_text(self, text, user, room):
        return self.fuzzy_center.get_merged_text(text, user, room)

    def saveRecord(self, prediction, message, text='', reason=''):
        if prediction == 0:
            # save to good sentence
            record = GoodSentence(
                message=message[:95],
                text=text[:63],
            )
        else:
            # save to blocked
            record = BlockedSentence(
                message=message[:95],
                text=text[:63],
                reason=reason[:63] if reason else '',
                status=int(prediction),
            )

        record.save()

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
