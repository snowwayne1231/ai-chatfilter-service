import re


regex_chinese = re.compile('[\u4e00-\u9fa5]+')

class PreFilter():
    white_words = []
    temporary_messages = []


    def __init__(self):
        self.white_words = []



    def find_special_char(self, text):
        next_char = ''
        for u in text:
            if not (self.is_chinese(u) or self.is_general(u) or self.is_full_character(u)):
                next_char += u
        return next_char

    
    def find_wechat_char(self, text, lowercase_only = True):
        next_char = ''
        for u in text:
            if self.is_number(u) or self.is_english(u):
                next_char += u
        return next_char if len(next_char) >= 6 else ''


    def is_chinese(self, uchar):
        return uchar >= u'\u4e00' and uchar <= u'\u9fa5'

    def is_zuyin(self, uchar):
        return uchar >= u'\u3105' and uchar <= u'\u312b'

    def is_general(self, uchar):
        return uchar >= u'\u0020' and uchar <= u'\u009b'

    def is_japan(self, uchar):
        return uchar >= u'\u3040' and uchar <= u'\u33ff'

    def is_full_character(self, uchar):
        #  _code > 0xfe00 and _code < 0xffff:
        # return (uchar >= u'\uff00' and uchar <= u'\uff65') or (uchar >= u'\ufe30' and uchar <= u'\ufe6a')
        return uchar >= u'\ufe30' and uchar <= u'\uff65'

    def is_number(self, uchar):
        # return (uchar >= u'\u0030' and uchar <= u'\u0039') or (uchar >= u'\uff10' and uchar <= u'\uff19')
        return uchar >= u'\u0030' and uchar <= u'\u0039'

    def is_english(self, uchar):
        # return (uchar >= u'\u0041' and uchar <= u'\u0039') or (uchar >= u'\u0061' and uchar <= u'\u007a')
        return uchar >= u'\u0061' and uchar <= u'\u007a'


    