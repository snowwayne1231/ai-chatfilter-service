import re


regex_chinese = re.compile('[\u4e00-\u9fa5]+')
regex_korea = re.compile('[\uac00-\ud7a3]+')
# single_blocked_words = ['㐅', '㐃', 'ㄥ', '鴞', '', '', '', '', '', '', '卩', 'ノ', 'ろ', '〇']
allowed_character_regexies = [
    (u'\u0020', u'\u0082'), # general english, digits and symbol
    (u'\u23e9', u'\u23f9'), # symbol
    # (u'\u26bd', u'\u270d'), # symbol
    (u'\u3001', u'\u3002'), # dot symbol
    # (u'\u3105', u'\u3129'), # zuyin
    (u'\u4e00', u'\u9fa5'), # chinese
    (u'\u3041', u'\u30ff'), # japanese
    # (u'\u1100', u'\u11f9'), # korea yin
    # (u'\u3131', u'\u318e'), # korea yin 2
    (u'\uac00', u'\ud7a3'), # korea
    (u'\uff01', u'\uff65'), # full type of english, digits and symbol
    # (u'\U0001f600', u'\U0001f64f'), # faces
    # (u'\U0001f910', u'\U0001f9ff'), # faces
]



class PreFilter():
    temporary_messages = []
    max_same_room_word = 2

    def __init__(self):
        self.temporary_messages = []

    
    
    def find_not_allowed_chat(self, text):
        next_char = ''

        text = self.replace_face_symbol(text)
        for u in text:
            if not self.is_allowed_character(u):
                next_char += u

        return next_char

    
    def find_korea_mixed(self, text):
        _korea_words = ''
        _korea_map = {}
        for u in text:
            if regex_korea.match(u):
                _korea_words += u
                if _korea_map.get(u):
                    _korea_map[u] += 1
                else:
                    _korea_map[u] = 1
        
        _length_korea = len(_korea_words)
        _length_text = len(text)
        _ratio = _length_korea / _length_text
        if _ratio == 1:
            _counting_double = 0
            for _kchar in _korea_map:
                if _korea_map[_kchar] > 1:
                    _counting_double += _korea_map[_kchar]

            _ratio_double = _counting_double / _length_korea
            if _ratio_double > 0.25:
                return _korea_words

        elif _length_korea >= 3:
            return _korea_words

        return ''

    
    def find_wechat_char(self, text, lowercase_only = True):
        number_size = 0
        eng_size = 0
        qk_size = 0
        next_char = ''
        _text_ = text.replace(' ', '')
        _has_wv = False
        
        length_char = len(_text_)

        if length_char == 0:
            return ''
    
        for u in _text_:
            if self.is_number(u):
                if '0' in next_char and u == '0':
                    continue
                number_size += 1
            elif self.is_english(u):
                eng_size += 1
                if u in 'vVwW':
                    _has_wv = True
            else:
                continue

            next_char += u

        _NE_size = number_size + eng_size

        _NE_ratio = _NE_size / length_char
        
        is_many_asci = (_NE_size >= 6 and number_size >= 2) or number_size > 4

        is_many_language = _NE_size >= 5 and _NE_ratio > 0.3 and _NE_ratio < 1 and (number_size > 0 or eng_size > 0)

        has_double_eng = False
        if _NE_ratio > 0.8 and eng_size > 5:
            __first_char = text[:2]
            # print('[find_wechat_char]__first_char: ', __first_char)
            __next_same_char = 0
            for __idx in range(len(text)):
                if __idx > 1 and text[__idx: __idx+2] == __first_char:
                    __next_same_char = __idx
                    break
            
            __first_sentence = text[:__next_same_char]
            # print('[find_wechat_char]__first_sentence: ', __first_sentence)
            
            if __next_same_char > 0 and len(__first_sentence) < 12:
                __left_text = text[__next_same_char:]
                # print('[find_wechat_char]__left_text: ', __left_text)

                if __first_sentence in __left_text:
                    has_double_eng = True

        # print('[find_wechat_char] _NE_ratio: ', _NE_ratio, ' | length_char: ', length_char, eng_size, number_size)
        
        # all is english and digits
        if _NE_ratio == 1 and number_size > 0 and length_char >= 3 and length_char <= 12:
           return next_char

        # print('[find_wechat_chat] _words:', _words)
        if _has_wv and eng_size < 3 and (length_char - eng_size) > 1:
            return next_char

        return next_char if is_many_asci or is_many_language or has_double_eng else ''

    
    def find_emoji_word_mixed(self, text):
        _r_emoji = r'\{\d{1,3}\}'
        _has_emoji = re.search(_r_emoji, text)
        if _has_emoji:
            _pured = re.sub(_r_emoji, '', text).strip()
            if len(_pured) > 0:
                return '#emoji#'
        return ''

    
    def find_unallow_eng(self, text):
        # 
        _unallow_engs = ['wei']
        for _ in _unallow_engs:
            if _ in text:
                return _
        return ''



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
        chineses = [
            u'\u4e00', u'\u58f9', u'\u4e8c', u'\u8cb3', u'\u4e09', u'\u53c1', u'\u56db', u'\u8086', u'\u4e94', u'\u4f0d', 
            u'\u5348', u'\u821e', u'\u516d', u'\u9678', u'\u4e03', u'\u67d2', u'\u516b', u'\u5df4', u'\u53ed', u'\u634c', 
            u'\u6252', u'\u4e5d', u'\u4e45', u'\u7396', u'\u9152', u'\u96f6', u'\u9748', '扒', '凌', '陵', '仁', '巴', '仇',
            '灵', '漆', '舞', '武', '医', '陆', '司', '饿', '久', '删', '酒', '林', '腰', '兰', '溜', '临', '寺', '期', '铃', '衫',
            '要', '山', '遛', '摇', '思', '妖', '贰', '玲', '是', '午', '妻', '跋', '衣', '似', '伶', '疤', '韭', '镹', '聆', '易',
            '死', '世', '芭', '令', '依', '市', '士', '吧', '伊', '柳', '斯', '珊', '流', '奇', '数', '趴', '灸', '凄', '淋', 
        ]
        return uchar >= u'\u0030' and uchar <= u'\u0039' or uchar in chineses

    def is_english(self, uchar):
        # return (uchar >= u'\u0041' and uchar <= u'\u0039') or (uchar >= u'\u0061' and uchar <= u'\u007a')
        return uchar >= u'\u0061' and uchar <= u'\u007a'

    def is_question_mark(self, uchar):
        return uchar == u'\u003f'


    def is_allowed_character(self, uchar):
        for _ in allowed_character_regexies:
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


    def check_same_room_conversation(self, _text, _before_room_texts):
        _num_matched = 0

        english_text = self.replace_only_left_english(_text)
        if english_text:
            if len(english_text) >= 4:
                for _rt in _before_room_texts:
                    if self.replace_only_left_english(_rt) == english_text:
                        return 'not allow same English keep typing'

        
        digital_text = self.replace_only_left_digital(_text)
        if digital_text and len(digital_text) >= 3:
            for _rt in _before_room_texts:
                if len(_rt) < 12:
                    _before_digital_text = self.replace_only_left_digital(_rt)
                    if len(_before_digital_text) >= 3:
                        return 'suspect digital merged wechat number'
                        

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

    def replace_only_left_digital(self, _text):
        return re.sub(r'[^(0-9)]+', '', _text)