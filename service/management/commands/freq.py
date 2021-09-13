from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, connections

from datetime import datetime
from dataparser.jsonparser import JsonParser
from dataparser.apps import JieBaDictionary
from ai.classes.translator_pinyin import translate_by_string
from ai.models import SoundVocabulary
from ai.service_impact import get_all_vocabulary_from_models

import os, time
import math


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
        _split_char = '_'
        _st_time = datetime.now()
        json_file_path = options.get('input_json')

        _jp = JsonParser(file=json_file_path)
        _jp.load()
        data_list = _jp.get_data_only_text()
        trasnlated_list = [translate_by_string(_) for _ in data_list]
        # print('data_list[10] : ', data_list[10])
        # print('trasnlated_list[10] : ', trasnlated_list[10])
        # exit(2)

        vocabulary_data = get_all_vocabulary_from_models()
        jieba_vocabulary = []
        jieba_freqs = []
        pinyin_data = vocabulary_data['pinyin']
        english_data = vocabulary_data['english']
        for pdata in pinyin_data:
            jieba_vocabulary.append(pdata[0])
            jieba_freqs.append(pdata[1])
        for edata in english_data:
            jieba_vocabulary.append(edata[0])
            jieba_freqs.append(edata[1])
    
        _jbd = JieBaDictionary(jieba_vocabulary, jieba_freqs)


        word_map = {}

        for _translated in trasnlated_list:
            _all_words = _jbd.get_cut_all(_translated, min_length=2)
            for _word in _all_words:
                _num = word_map.get(_word)
                _split_length = _word.count(_split_char)
                _word_length = _split_length if _split_length > 0 else len(_word)
                if _num:
                    if _word_length <= 2:
                        if _num > 64:
                            word_map[_word] += 1 / round(math.log(word_map[_word], 2))
                        else:
                            word_map[_word] += 1
                    else:
                        word_map[_word] += _word_length
                else:
                    word_map[_word] = 1+(2**(_word_length-1))
            
            # print('[]translated sentence: {}  |  _all_words: {}'.format(_translated, _all_words))

        # print('word_map: ', word_map)

        result_list = sorted(word_map.items(), key=lambda x:x[1], reverse=True)
        print('Top 10 Results: ')
        
        print(result_list[:10])
        print('Bottom 10 Results: ')
        print(result_list[-10:])

        # new_json = JsonParser(file=os.path.dirname(json_file_path) + '/output.freq.json')
        # new_json.save(result_list)

        _all_sv = SoundVocabulary.objects.all()
        _sv_map_instances = {}
        for _sv in _all_sv:
            _sv_map_instances[_sv.pinyin] = _sv


        _max_freq = 999
        _pr = 0

        for _r in result_list:
            _word = _r[0]
            _freq = round(_r[1])
            _instance = _sv_map_instances[_word]
            _next_freq = min(_freq, _max_freq)
            _instance.freq = _next_freq
            _instance.save()

            _gap = _max_freq - _freq
            _next_pr = _gap / _max_freq

            if _next_pr > _pr + 0.01:
                _pr = _next_pr
                print(' {:2.2f}%'.format(_pr * 100), end='\r')

        
        _ed_time = datetime.now()
        print('Setting Vocabulary FREQ Success. Spend Time: ', _ed_time - _st_time)


        