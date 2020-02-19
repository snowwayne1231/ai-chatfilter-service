import re


regex_chinese = re.compile('[\u4e00-\u9fa5]+')

class PreFilter():
    white_words = []
    temporary_messages = []


    def __init__(self):
        self.white_words = []



    def find_special_char(self, text):
        next_char = ''
        size_qk = 0
        
        for u in text:
            if self.is_rare_character(u):
                next_char += u
            elif self.is_question_mark(u):
                size_qk += 1

        is_too_many_question_marks = size_qk >= 3

        return '?' if is_too_many_question_marks else next_char

    
    def find_wechat_char(self, text, lowercase_only = True):
        number_size = 0
        eng_size = 0
        qk_size = 0
        next_char = ''
        length_char = len(text)

        for u in text:
            if self.is_number(u):
                if '0' not in next_char:
                    number_size += 1
            elif self.is_english(u):
                eng_size += 1
            else:
                continue

            next_char += u

        _NE_size = number_size + eng_size

        _NE_ratio = _NE_size / length_char
        
        is_many_asci = (_NE_size >= 6 and number_size >= 2) or number_size > 4

        is_many_language = _NE_ratio > 0.3 and _NE_ratio < 1 and number_size > 0 and eng_size > 0

        # is_many_mixed = _NE_size >= 6 and (length_char - _NE_size) > 4

        return next_char if is_many_asci or is_many_language else ''


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
        chineses = [u'\u4e00', u'\u58f9', u'\u4e8c', u'\u8cb3', u'\u4e09', u'\u53c1', u'\u56db', u'\u8086', u'\u4e94', u'\u4f0d', u'\u5348', u'\u821e', u'\u516d', u'\u9678', u'\u4e03', u'\u67d2', u'\u516b', u'\u5df4', u'\u53ed', u'\u634c', u'\u6252', u'\u4e5d', u'\u4e45', u'\u7396', u'\u9152', u'\u96f6', u'\u9748']
        return uchar >= u'\u0030' and uchar <= u'\u0039' or uchar in chineses

    def is_english(self, uchar):
        # return (uchar >= u'\u0041' and uchar <= u'\u0039') or (uchar >= u'\u0061' and uchar <= u'\u007a')
        return uchar >= u'\u0061' and uchar <= u'\u007a'

    def is_question_mark(self, uchar):
        return uchar == u'\u003f'

    def is_rare_character(self, uchar):
        is_rare_symbol = (uchar >= u'\u0080' and uchar <= u'\u0e00') or (uchar >= u'\u0fff' and uchar <= u'\u1100') or (uchar >= u'\u1b7f' and uchar <= u'\u2e7f')
        is_sp_symbol = uchar >= u'\u3190' and uchar <= u'\u31bf'
        is_odd_symbol = uchar >= u'\u3200' and uchar <= u'\u33ff'
        is_odd_symbol_2 = uchar >= u'\u4db0' and uchar <= u'\u4dff'
        is_odd_symbol_3 = uchar >= u'\ua000' and uchar <= u'\uac00'
        is_odd_symbol_4 = uchar >= u'\ud7b0' and uchar <= u'\ufe2f'
        is_odd_symbol_5 = uchar >= u'\ufe70' and uchar <= u'\uffff'

    