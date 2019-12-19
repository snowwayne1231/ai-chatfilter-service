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
        number_size = 0
        eng_size = 0
        next_char = ''
        length_char = len(text)

        for u in text:
            if self.is_number(u):
                number_size += 1
                next_char += u
            elif self.is_english(u):
                eng_size += 1
                next_char += u
        
        is_many_asci = len(next_char) >= 6 and number_size >= 2 and eng_size <= 24

        _NE_size = number_size + eng_size
        is_less_meaning = length_char > 0 and _NE_size != length_char and _NE_size / length_char > 0.8 and length_char <= 6

        return next_char if is_many_asci or is_less_meaning else ''


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


    