from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, connections

from datetime import datetime
from dataparser.jsonparser import JsonParser
from dataparser.apps import JieBaDictionary
from ai.classes.translator_pinyin import translate_by_string
from ai.models import SoundVocabulary

import os, time


class Command(BaseCommand):
    help = "counting FREQ for sentences."

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_json', required=True,
            help='path of input json file.',
        )
        # parser.add_argument(
        #     '-a', dest='app_name', required=False,
        #     help='the name of app.',
        # )

    def handle(self, *args, **options):
        _st_time = datetime.now()
        json_file_path = options.get('input_json')

        _jp = JsonParser(file=json_file_path)
        _jp.load()
        data_list = _jp.get_data_only_text()
        trasnlated_list = [translate_by_string(_) for _ in data_list]
    
        _jbd = JieBaDictionary()

        word_map = {}

        for _translated in trasnlated_list:
            _all_words = _jbd.get_cut_all(_translated, min_length=2)
            for _word in _all_words:
                _num = word_map.get(_word)
                if _num:
                    word_map[_word] += 1
                else:
                    word_map[_word] = 1
            
            # print('[]translated sentence: {}  |  _all_words: {}'.format(_translated, _all_words))


        # print('word_map: ', word_map)

        result_list = sorted(word_map.items(), key=lambda x:x[1], reverse=True)

        # print(result_list)

        # new_json = JsonParser(file=os.path.dirname(json_file_path) + '/output.freq.json')
        # new_json.save(result_list)

        _all_sv = SoundVocabulary.objects.all()
        _sv_map_instances = {}
        for _sv in _all_sv:
            _sv_map_instances[_sv.pinyin] = _sv


        _max_freq = 3000
        _pr = 0

        for _r in result_list:
            _word = _r[0]
            _freq = _r[1]
            _instance = _sv_map_instances[_word]
            _next_freq = min(_freq, _max_freq)
            _instance.freq = _next_freq
            _instance.save()

            _gap = _max_freq - _freq
            _next_pr = _gap / _max_freq

            if _next_pr > _pr + 0.01:
                _pr = _next_pr
                print(' {:2.2f}%'.format(_pr * 100), end='\r')

            if _freq <= 5:
                break
        
        _ed_time = datetime.now()
        print('Setting Vocabulary FREQ Success. Spend Time: ', _ed_time - _st_time)


        