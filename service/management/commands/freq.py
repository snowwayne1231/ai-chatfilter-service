from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, connections

from datetime import datetime
from dataparser.jsonparser import JsonParser
from dataparser.apps import JieBaDictionary
from ai.classes.translator_pinyin import translate_by_string

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

        new_json = JsonParser(file=os.path.dirname(json_file_path) + '/output.json')
        new_json.save(result_list)
        
        _ed_time = datetime.now()
        print('Spend Time: ', _ed_time - _st_time)


        