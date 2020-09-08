from django.utils import timezone
from django.conf import settings
import numpy as np
import time, re
from service.widgets import printt



class NicknameFilter():
    """

    """

    CODE_SUSPECT_AD = 1
    CODE_DIRTY_WORD = 2
    CODE_INVALID_PATTERN = 3
    CODE_SYSTEM_FAILURE = 4

    STATUS_MODE_CHINESE = 1
    STATUS_MODE_ENGLISH = 2

    regex_is_eng = re.compile('[a-zA-Z]')
    lang_mode = 1

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

        logging.info('Nickname Filter Language [{}]'.format(_setting))


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
        for _ in nickname:
            if _.isdigit():
                digits += 1
            elif self.regex_is_eng.match(_):
                eng += 1

        if digits > 0 and digits + eng >= 3:
            return self.CODE_INVALID_PATTERN

        return 0


    def think_english(self, nickname):
        return 0