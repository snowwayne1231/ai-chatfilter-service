from ai.apps import MainAiApp
from dataparser.apps import MessageParser
from .classes.prefilter import PreFilter
from .classes.fuzzycenter import FuzzyCenter
import numpy as np



class MainService():
    pre_filter = None
    ai_app = None
    message_parser = None
    fuzzy_center = None
    STATUS_PREDICTION_NO_MSG = -1
    STATUS_PREDICTION_SPECIAL_CHAR = -2
    STATUS_PREDICTION_NONSENSE = -3
    STATUS_PREDICTION_WEHCAT_SUSPICION = -4

    def __init__(self):
        self.ai_app = MainAiApp()
        self.message_parser = MessageParser()

        
        self.pre_filter = PreFilter()
        self.fuzzy_center = FuzzyCenter()

    
    def parse_message(self, string):
        return self.message_parser.parse(string)


    def think(self, message, user = '', room = ''):
        result = {}
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
                
                        prediction = self.ai_app.predict(merged_text, lv=lv)
                    

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
