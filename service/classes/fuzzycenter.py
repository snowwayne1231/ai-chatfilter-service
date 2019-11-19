from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from datetime import datetime 

class FuzzyCenter():
    """
    """
    user_define_ratio = 80
    wording_define_ratio = 60
    temporary_text_list = []
    temporary_timereserve = 0


    def __init__(self):
        self.temporary_timereserve = 3 * 60 # 3 minitues


    def upsert_temp_text(self, text, user, room, lv, anchor, prediction):
        _now = datetime.now()
        _timestamp = datetime.timestamp(_now)

        self.temporary_text_list = [_ for _ in self.temporary_text_list if (_[0] + self.temporary_timereserve) > _timestamp]

        _loc = [_timestamp, text, user, room, lv, anchor, prediction]

        self.temporary_text_list.insert(0, _loc)

        # print(self.temporary_text_list)

        return self


    def get_temp_texts(self, user, room):
        return [_ for _ in self.temporary_text_list if fuzz.ratio(_[2], user) > self.user_define_ratio and _[3] == room and _[6] == 0]


    def get_merged_text(self, text, user, room):
        texts = self.get_temp_texts(user, room)
        if len(texts) == 0:
            return text

        lastest_text = texts[0]
        res_text = ''

        if len(text) < 3:
            res_text = lastest_text[1] + text
            
        else:        
            _now = datetime.now()
            _timestamp = datetime.timestamp(_now)
            if _timestamp - lastest_text[0] < 10:
                res_text = lastest_text[1] + text
            else:
                return text
        
        return res_text if len(res_text) > 0 else None