from django.utils import timezone
from django.conf import settings
import numpy as np
import time, re
from service.widgets import printt
from service.classes.unicode import find_not_allowed_chat, parse_to_half_char, is_mix_multiple_language



class NicknameFilter():
    """

    """

    CODE_SUSPECT_AD = 1
    CODE_DIRTY_WORD = 2
    CODE_INVALID_PATTERN = 3
    CODE_SYSTEM_FAILURE = 4
    CODE_UNAUTHORITY = 5
    CODE_MULTIPLE_LANGUAGE = 6

    STATUS_MODE_CHINESE = 1
    STATUS_MODE_ENGLISH = 2

    regex_is_eng = re.compile('[a-zA-Z]')
    lang_mode = 1
    english_parser = None

    def __init__(self, is_admin=True, lang_mode=0):
        if lang_mode == 0:
            self.init_language()
        
        _now = timezone.now()
        today_datetime = timezone.localtime(_now)


    def init_language(self):
        _setting = settings.LANGUAGE_MODE
        if _setting == 'EN':
            self.lang_mode = self.STATUS_MODE_ENGLISH
        else:
            self.lang_mode = self.STATUS_MODE_CHINESE


    def think(self, nickname):
        result = {
            'code': 0
        }

        if self.lang_mode == self.STATUS_MODE_CHINESE:

            result['code'] = self.think_chinese(nickname)

        elif self.lang_mode == self.STATUS_MODE_ENGLISH:

            result['code'] = self.think_english(nickname)

        return result


    def think_chinese(self, nickname):
        digits = 0
        eng = 0
        nickname = parse_to_half_char(nickname)
        # print('[think_chinese] parsed nickname: ', nickname)
        for _ in nickname:
            if _.isdigit():
                digits += 1
            elif self.regex_is_eng.match(_):
                eng += 1

        if digits > 0 and digits + eng >= 3:
            return self.CODE_INVALID_PATTERN

        if find_not_allowed_chat(nickname):
            return self.CODE_UNAUTHORITY

        if is_mix_multiple_language(nickname):
            _eng_text = self.english_parser.replace_to_only_english(nickname)
            _eng_list = self.english_parser.parse_right_vocabulary_list(_eng_text)
            if len(_eng_list) == 0:
                return self.CODE_MULTIPLE_LANGUAGE

        elif eng >= 6:
            return self.CODE_INVALID_PATTERN

        return 0


    def think_english(self, nickname):
        return 0


    def set_english_parser(self, parser_instance):
        self.english_parser = parser_instance
        print('[NicknameFilter] Set English Parser Vocabulary Length: ', len(self.english_parser.get_vocabulary()))