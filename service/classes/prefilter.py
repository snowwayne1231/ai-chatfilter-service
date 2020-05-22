import re


regex_chinese = re.compile('[\u4e00-\u9fa5]+')

class PreFilter():
    temporary_messages = []
    max_same_room_word = 2
    single_words = []

    def __init__(self):
        self.temporary_messages = []


    def find_special_char(self, text):
        next_char = ''
        size_qk = 0

        text = self.replace_face_symbol(text)
        
        for u in text:
            if self.is_rare_character(u):
                next_char += u
            elif self.is_question_mark(u):
                size_qk += 1

        is_too_many_question_marks = size_qk >= 3
        # if next_char:
        #     return next_char

        return '?' if is_too_many_question_marks else next_char

    
    def find_wechat_char(self, text, lowercase_only = True):
        number_size = 0
        eng_size = 0
        qk_size = 0
        next_char = ''
        has_space = bool(' ' in text)
        if has_space:
            text = text.replace(' ', '')
        
        length_char = len(text)

        if length_char == 0:
            return ''
    
        for u in text:
            if self.is_number(u):
                if '0' not in next_char:
                    number_size += 1
                    # print('is number: ', u)
            elif self.is_english(u):
                eng_size += 1
            else:
                continue

            next_char += u

        _NE_size = number_size + eng_size

        _NE_ratio = _NE_size / length_char
        
        is_many_asci = (_NE_size >= 6 and number_size >= 2) or number_size > 5

        is_many_language = _NE_size >= 5 and _NE_ratio > 0.3 and _NE_ratio < 1 and number_size > 0 and eng_size > 0

        # print('[find_wechat_char] _NE_ratio: ', _NE_ratio, ' | length_char: ', length_char, eng_size, number_size)

        if _NE_ratio == 1 and length_char >= 3 and length_char <= 9:
            _english = self.replace_only_left_english(text)
            # print('[find_wechat_chat] _english:', _english)
            
            if _english in self.single_words:
                pass
            else:
                _buf = ''
                _tmp_word = ''
                _words = []
                for _ in _english:
                    _buf += _
                    if _buf in self.single_words:
                        _tmp_word = _buf
                    else:
                        if _tmp_word:
                            _words.append(_tmp_word)
                            _tmp_word = ''
                            _buf = _
                
                if _tmp_word == _buf:
                    _words.append(_tmp_word)
                else:
                    is_many_language = True
                    next_char += ' | Wrong English Words.'

        # print('[find_wechat_chat] _words:', _words)

        return next_char if is_many_asci or is_many_language else ''


    def is_chinese(self, uchar):
        return (uchar >= u'\u4e00' and uchar <= u'\u9fa5') or (uchar >= u'\uf970' and uchar <= u'\ufa6d')

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
        regexies = [
            (u'\u0083', u'\u0083'), # suspect english
            (u'\u008a', u'\u00a3'), # suspect english
            (u'\u00a9', u'\u00b6'), # suspect english
            (u'\u00b9', u'\u02b8'), # suspect english
            (u'\u0363', u'\u058f'), # suspect english
            (u'\u05d0', u'\u0dff'), # suspect english
            (u'\u0fff', u'\u1100'), # rare symbol
            (u'\u13a0', u'\u1a1f'), # rare symbol 
            (u'\u1b7f', u'\u1fff'), # rare symbol
            (u'\u203d', u'\u23e8'), # rare symbol so many close to be suspect
            (u'\u23fb', u'\u2647'), # rare symbol so many close to be suspect
            (u'\u26a2', u'\u26bc'), # rare symbol so many close to be suspect
            (u'\u2710', u'\u271f'), # rare symbol and suspect digits
            (u'\u2776', u'\u2b4f'), # rare symbol and suspect digits
            (u'\u2bd0', u'\u2e7f'), # rare symbol and suspect digits
            (u'\u3190', u'\u31bf'), # special zuyin
            (u'\u3200', u'\u33ff'), # special number
            (u'\u4db0', u'\u4dff'), # none sense
            (u'\ua000', u'\uabff'), # roma special
            (u'\ud7b0', u'\uf8ff'), # unknown
            (u'\ufe70', u'\uff00'),
            (u'\uff10', u'\uff19'), # full digits
            (u'\uff21', u'\uff3a'), # full english
            (u'\uff41', u'\uff5a'), # full english
            (u'\uffa0', u'\uffe1'),
            (u'\uffe6', u'\uffff'),
            (u'\U0001f000', u'\U0001f2ff'), # utf-16 special number and english
            (u'\U0001f519', u'\U0001f524'), # utf-16 suspect english
            (u'\U0001f5da', u'\U0001f5db'), # utf-16 suspect english
            (u'\U0001f700', u'\U0001f7a7'), # utf-16 suspect english
            # (u'\U00020000', u'\U0002cfff'), # rare chinese
        ]
        
        # print('uchar: ', uchar.encode('unicode_escape'))
        for _ in regexies:
            _st = _[0]
            _ed = _[1]
            if uchar <= _ed:
                if uchar >= _st:
                    return True
                break

        return False


    def replace_face_symbol(self, _text):
        regexs = [
            r'°□°',
            r'＾∀＾',
            r'✿‿✿',
            r'´◡`',
            r'༼ つ ◕_◕ ༽つ',
            r'◕_◕',
            r'✪▽✪',
            r'(ง •̀_•́)ง',
            r'(•̀⌄•́)',
            r'ฅ՞•ﻌ•՞ฅ',
            r'(◔.̮◔)',
            r'(ღ♡‿♡ღ)',
            r'(○^㉨^)',
        ]
        for _r in regexs:
            _text = re.sub(_r, '', _text)
        return _text


    def set_single_words(self, words):
        _word_list = [self.replace_only_left_english(_) for _ in words]
        self.single_words = [_ for _ in _word_list if _]


    def check_same_room_conversation(self, _text, _before_room_texts):
        _num_matched = 0

        english_text = self.replace_only_left_english(_text)
        if english_text:
            if len(english_text) >= 4:
                for _rt in _before_room_texts:
                    if self.replace_only_left_english(_rt) == english_text:
                        return 'not allow same English keep typing'
                        # _num_matched += 1
                        # if _num_matched >= self.max_same_room_word:
                        #     return 'too many same English'
                        

        bankerplayer_text = self.replace_only_left_bankerplayer(_text)

        if bankerplayer_text:
            for _rt in _before_room_texts:
                # if len(_rt) >= 10:
                #     continue
                if self.replace_only_left_bankerplayer(_rt):
                    _num_matched += 1
                    if _num_matched > self.max_same_room_word:
                        return 'too many talked on banker and player'

        return ''


    def replace_only_left_english(self, _text):
        return re.sub(r'[^(a-zA-Z)]+', '', _text)

    def replace_only_left_bankerplayer(self, _text):
        return re.sub(r'[^(莊庄装閒閑闲贤)]+', '', _text)