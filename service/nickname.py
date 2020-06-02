from django.utils import timezone
import numpy as np
import time, re
from service.widgets import printt



class NicknameFilter():
    """

    """

    CODE_TOO_MANY_ENGLISH_AND_DIGITAL = 1
    regex_is_eng = re.compile('[a-zA-Z]')

    def __init__(self, is_admin=True):
        _now = timezone.now()
        today_datetime = timezone.localtime(_now)


    def think(self, nickname):
        result = {
            'code': 0
        }
        digits = 0
        eng = 0
        for _ in nickname:
            if _.isdigit():
                digits += 1
            elif self.regex_is_eng.match(_):
                eng += 1

        if digits > 0 and digits + eng >= 3:
            result['code'] = self.CODE_TOO_MANY_ENGLISH_AND_DIGITAL
        
        return result
