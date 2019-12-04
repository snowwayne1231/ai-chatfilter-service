from ai.apps import MainAiApp
from dataparser.apps import MessageParser
from .classes.prefilter import PreFilter
from .classes.fuzzycenter import FuzzyCenter
from .models import GoodSentence, BlockedSentence
import numpy as np



class MainService():
    pre_filter = None
    ai_app = None
    message_parser = None
    fuzzy_center = None
    STATUS_PREDICTION_NO_MSG = 10
    STATUS_PREDICTION_SPECIAL_CHAR = 11
    STATUS_PREDICTION_NONSENSE = 12
    STATUS_PREDICTION_WEHCAT_SUSPICION = 13
    STATUS_PREDICTION_BLOCK_WORD = 14

    def __init__(self):
        self.ai_app = MainAiApp()
        self.message_parser = MessageParser()

        
        self.pre_filter = PreFilter()
        self.fuzzy_center = FuzzyCenter()

    
    def parse_message(self, string):
        return self.message_parser.parse(string)


    def think(self, message, user = '', room = '', silence=False):
        result = {}
        text = ''
        reason_char = ''
        # print('receive message :', message)

        if message:
            reason_char = self.pre_filter.find_special_char(message)

            if reason_char:
                prediction = self.STATUS_PREDICTION_SPECIAL_CHAR

            else:
                text, lv, anchor = self.parse_message(message)
                
                merged_text = self.get_merged_text(text, user, room)
                if merged_text is None:

                    prediction = self.STATUS_PREDICTION_NONSENSE

                else:

                    reason_char = self.pre_filter.find_wechat_char(merged_text)

                    if reason_char:

                        prediction = self.STATUS_PREDICTION_WEHCAT_SUSPICION

                    else:
                        
                        reason_char = self.fuzzy_center.find_fuzzy_block_word(merged_text, silence=silence)

                        if reason_char:

                            prediction = self.STATUS_PREDICTION_BLOCK_WORD

                        else:

                            prediction, reason_char = self.ai_app.predict(merged_text, lv=lv, silence=silence)

                            self.store_temporary_text(
                                text=text,
                                user=user,
                                room=room,
                                lv=lv,
                                anchor=anchor,
                                prediction=prediction,
                            )
                        
        else:

            prediction = self.STATUS_PREDICTION_NO_MSG

        # print('prediction :', prediction)
        if not silence:
            self.saveRecord(prediction, message=message, text=text, reason=reason_char)
        
        
        
        result['user'] = user
        result['room'] = room
        result['message'] = message
        result['prediction'] = prediction
        result['reason_char'] = reason_char

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