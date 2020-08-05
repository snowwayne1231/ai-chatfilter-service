from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig

from datetime import datetime
from .classes.map_hex import mapHexes
from .models import CustomDictionaryWord
from .jsonparser import JsonParser
from service.models import Blockword
from ai.models import SoundVocabulary, NewVocabulary, DigitalVocabulary, Vocabulary, Language
from ai.classes.translator_pinyin import translate_by_string

import xlrd, openpyxl
import os
import re
import jieba
import pickle


class DataparserConfig(AppConfig):
    name = 'dataparser'




class ExcelParser():
    """
        get_row_list (column=[], limit=0)
        return List
    """
    file = None
    books = []
    is_multiple = False
    file_extension = re.compile("^(.*).xlsx?$", re.IGNORECASE)

    def __init__(self, **kwargs):

        self.file = kwargs.get(
            'file',
            None,
        )

        if self.file:
            start_time = datetime.now()

            if os.path.isdir(self.file):

                self.is_multiple = True

                for _file in os.listdir(self.file):

                    if self.file_extension.search(_file):

                        _file_path = '{}/{}'.format(self.file, _file)
                        print('ExcelParser Open File Path: ', _file_path)
                        book = xlrd.open_workbook(_file_path)
                        self.books.append(book)

            else:

                self.is_multiple = False
                book = xlrd.open_workbook(self.file)
                # self.book = book
                self.books.append(book)


            end_time = datetime.now()
            spend_second = (end_time - start_time).total_seconds()

            print('====ExcelParser Loads File spend seconds: ', spend_second)
            print("Worksheet name(s): {0}".format(book.sheet_names()))

        else:

            print('ExcelParser Failed With Wrong File path.')


    def get_row_list(self, column=[], limit=0, just_first_sheet=True):
        total_rows = []
        _book_idx = 1
        for book in self.books:

            if just_first_sheet:
                sheet = book.sheet_by_index(0)
                rows = self.get_row_list_by_sheet(sheet, column=column, limit=limit)
                total_rows += rows
                print('Excel Get Row List: Book Index[{}] Row Length: {}'.format(_book_idx, len(rows)))

            _book_idx += 1

        return total_rows
    
    def get_row_list_by_sheet(self, sheet, column=[], limit=0):
        sh = sheet
        # print("==Getting Data in Sheet name: {0}, rows: {1}, cols:{2}".format(sh.name, sh.nrows, sh.ncols))
        ary = []
        _columns = []

        def parse_str(value):
            if isinstance(value, str):
                return value
            elif isinstance(value, int):
                return str(value)
            else:
                return str(int(value))
            
        if len(column) > 0:
        
            for rx in range(limit if limit > 0 else sh.nrows):
                
                child = [x.value for x in sh.row(rx)]
                if rx == 0:
                    for col in column:
                        if type(col) == list:
                            __idx = -1
                            for __c in col:
                                __loc_idx = child.index(__c) if __c in child else -1
                                if __loc_idx >= 0:
                                    __idx = __loc_idx
                                    break
                        else:
                            __idx = child.index(col) if col in child else -1

                        _columns.append(__idx)

                else:
                    
                    _next_child = [parse_str(child[i]) if i >= 0 else '' for i in _columns]
                    ary.append(_next_child)
        else:

            for rx in range(limit if limit > 0 else sh.nrows):

                child = [parse_str(x.value) for x in sh.row(rx)]
                ary.append(child)
        

        return ary


    def export_excel(self, file=None, data=[]):
        _new_book = openpyxl.Workbook()
        _newsheet = _new_book.create_sheet(index=0)

        _r = 1
        for _ in data:
            _c = 1
            for loc in _:
                if loc.isdigit():
                    _newsheet.cell(_r, _c).value = int(loc)
                else:
                    _newsheet.cell(_r, _c).value = loc
                _c += 1
            _r += 1

        if file:
            print('Save Trim File: ', file)
            _new_book.save(file)
        


class MessageParser():

    regex_msg = re.compile("<msg>(.*)</msg>", flags= re.IGNORECASE | re.DOTALL)
    regex_xml_lv = re.compile("<[a-z]*?lv>(.*?)</[a-z]*?lv>", flags= re.IGNORECASE | re.DOTALL)
    regex_xml_anchor = re.compile("<anchmsg>(.*)</anchmsg>", flags= re.IGNORECASE | re.DOTALL)
    regex_xml_anchor_2 = re.compile("<isAnchorPlatformMsg>(.*)</isAnchorPlatformMsg>", flags= re.IGNORECASE | re.DOTALL)
    regex_xml_anchor_3 = re.compile("<anchor>(.*)</anchor>", flags= re.IGNORECASE | re.DOTALL)

    regex_xml_tag = re.compile("<[^>]+?>[^<]*?</[^>]+?>")
    # regex_xml_at = re.compile("<at>(.*)</at>", flags= re.IGNORECASE | re.DOTALL)
    regex_xml_broke_start = re.compile("(<msg>)|(<.*$)", flags= re.IGNORECASE)
    regex_xml_broke_end = re.compile("<[^>]+?$")

    regex_bracket_lv = re.compile("\{viplv(.+?)\}", flags= re.IGNORECASE | re.DOTALL)
    regex_bracket_digits = re.compile("\{[a-zA-Z\d\s\:\-]*\}")

    def __init__(self):
        print('MessageParser init done.')

    
    def parse(self, string):
        lv = 0
        anchor = 0
        repres_msg = None
        # try:
        #     repres_msg = self.regex_msg.match(string)
        # except Exception as ex:
        #     print('string: ', string)
        #     print(ex)
        repres_msg = self.regex_msg.match(string)

        if repres_msg:

            text = repres_msg.group(1)
            # print('string: ', string)
            # print('text: ', text)
            repres_xml_lv = self.regex_xml_lv.search(text)
            if repres_xml_lv:
                lv = int(repres_xml_lv.group(1))

            repres_xml_anchor = self.regex_xml_anchor.search(text)
            if repres_xml_anchor:
                anchor = int(repres_xml_anchor.group(1))
            else:
                repres_xml_anchor = self.regex_xml_anchor_2.search(text)
                if repres_xml_anchor:
                    anchor = int(repres_xml_anchor.group(1))
                elif self.regex_xml_anchor_3.search(text):
                    anchor = 1
            
            # at_msg = self.regex_xml_at(text)
            # if at_msg:
            #     text = at_msg.group(1)
            # else:

            text = self.regex_xml_tag.sub("", text)
            
        else:

            text = string.strip()

            repres_bracket_lv = self.regex_bracket_lv.match(text)

            if repres_bracket_lv:
                
                lv = int(repres_bracket_lv.group(1))
                text = self.regex_bracket_lv.sub("", text)

            else:

                repres_xml_lv = self.regex_xml_lv.search(text)
                if repres_xml_lv:
                    # broke message..
                    lv = int(repres_xml_lv.group(1))
                    text = self.regex_xml_tag.sub("", text)
                    text = self.regex_xml_broke_start.sub("", text)
                    text = self.regex_xml_broke_end.sub("", text)


        text = self.regex_bracket_digits.sub("", text)
        text = self.trim_only_general_and_chinese(text)
        
        # print(text, lv, anchor)

        return text, lv, anchor

    
    def trim_only_general_and_chinese(self, string):
        _result = ''

        for uc in string:
            _code = ord(uc)

            if _code >= 0x4e00 and _code <= 0x9faf:
                # chinese
                _result += uc
                continue
            elif _code == 0x3000:
                # full space to half space
                _code = 0x0020
            elif _code > 0xfee0 and _code < 0xffff:
                # full char to half
                _code -= 0xfee0
            
            # 【2000-206F】 General Punctuation 一般標點符號 # 8216
            # if _code >= 0x2000 and _code <= 0x206f: continue
            # 【3000-303F】 CJK Symbols and Punctuation 中日韓符號和標點  # 12290
            # if _code >= 0x3000 and _code <= 0x303f: continue

            if _code == 0x0020 or (_code >= 0x0030 and _code <= 0x0039) or (_code >= 0x0041 and _code <= 0x005a) or (_code >= 0x0061 and _code <= 0x007a):
                _result += chr(_code).lower()

            # if (_code < 0x0030 and _code != 0x0020) or 
            #     _code > 0x7f or 
            #     (_code >= 0x3a and _code <= 0x40 ):
            #     continue
                # out of English or digits
                # _hex16 = hex(_code)
                # _string = mapHexes.get(_code, None)
                
                # if _string:
                #     _result += _string
            # else:
            #     _result += chr(_code).lower()
        
        return _result



class JieBaDictionary():
    """
        
    """
    split_character = '_'
    unknown_character = '#UNK#'
    pad_character = '#PAD#'
    number_character = '#NUM#'
    alphabet_character = '#ALP#'
    reserve_character = '#RES#'
    folder = os.path.dirname(__file__)
    pickle_folder = os.path.dirname(__file__) + '/_pickles'
    freq_json_file = os.path.dirname(__file__) + '/assets/freq.json'
    origin_vocabulary = []
    vocabularies = []
    vocabulary_freqs = []
    none_tone_map = {}
    re_eng = re.compile('[a-zA-Z0-9_]', re.U)

    _jsonparser = None

    def __init__(self, vocabulary=[]):
        self.origin_vocabulary = [self.pad_character, self.unknown_character, self.number_character, self.alphabet_character, self.reserve_character]
        jieba.re_eng = self.re_eng
        jieba.initialize(dictionary=self.folder + '/assets/jieba.txt')
        self._jsonparser = JsonParser(file=self.freq_json_file)

        if not os.path.isdir(self.pickle_folder):
            os.mkdir(self.pickle_folder)

        if len(vocabulary) == 0:
            # self.load_vocabularies()
            self.refresh_dictionary()
        else:
            self.load_vocabularies(vocabulary=vocabulary)
            self.save_vocabularies()
        
        
        print('JieBaDictionary Initial Done.')


    def split_word(self, text=''):
        # _list = jieba.cut(text, HMM=False, cut_all=False) if text else []
        results = []
        unknowns = []
        _buf = ''

        _list = self.__cut_DAG_NO_HMM(text)

        for _ in _list:
            # print('[split_word] _: ', _)
            if not _:
                continue
            elif  _[-1] == self.split_character:

                if _buf:
                    __ = _buf + _
                    _buf = ''
                    if __[:-1].isdigit():
                        # print('[split_word] [isdigit] number_character __: ', __)
                        _none_tone_words = self.get_none_tone_word(__)
                        # print('[split_word] [isdigit] _none_tone_words: ', _none_tone_words)
                        if _none_tone_words:
                            results += _none_tone_words
                        else:
                            results.append(self.number_character)
                        
                        continue

                    _none_tone_words = self.get_none_tone_word(__)
                    # print('[split_word] _none_tone_words: ', _none_tone_words)
                    if _none_tone_words:
                        # print('_none_tone_words: {},  origin: {}'.format(_none_tone_words, __))
                        results += _none_tone_words
                    else:
                        if __.count(self.split_character) > 1:
                            __words = __.split(self.split_character)
                            _map = self.none_tone_map
                            for _word in __words:
                                if _word:
                                    if _map.get(_word, None):
                                        results.append(_word+self.split_character)
                                    else:
                                        results.append(self.unknown_character)
                                        unknowns.append(_word+self.split_character)
                        else:
                            results.append(self.unknown_character)
                            unknowns.append(__)
                    
                else:
                    __ = _

                    if len(__) > 1:
                        if __[:-1].isdigit():
                            # print('[split_word] number_character __: ', __)
                            _none_tone_words = self.get_none_tone_word(__)
                            # print('[split_word] [isdigit] _none_tone_words: ', _none_tone_words)
                            if _none_tone_words:
                                results += _none_tone_words 
                            else:
                                results.append(self.number_character)
                            
                        else:
                            results.append(__)

            else:
                _buf += _
                # print('split_word buffer add: ', _buf)
                # print('text: ', text)

        if _buf:
            print('split_word [] Why left _buf: ', _buf)
            print('split_word [] text: ', text)
            unknowns.append(_buf)
        
        # print('[split_word] origin text: ', text)
        # print('[split_word] results: ', results)
        # print('[split_word] unknowns: ', unknowns)
        return results, unknowns


    def __cut_DAG_NO_HMM(self, sentence):
        _DAG = jieba.get_DAG(sentence)
        # print('[__cut_DAG_NO_HMM] sentence: ', sentence)
        # print('[__cut_DAG_NO_HMM] DAG: ', _DAG)
        route = {}

        _FREQ = jieba.dt.FREQ
        _split_char = self.split_character
        _list_splited_idx = []

        # N = len(sentence)
        # route[N] = (0, 0)
        # for _idx in range(N - 2, -1, -1):
        #     if _idx == 0 or sentence[_idx-1] == _split_char:
        #         for _x in _DAG[_idx]:
        #             _sen = sentence[_idx:_x + 1]
        #             _freq_ = _FREQ.get(_sen)


        jieba.calc(sentence, _DAG, route)
        x = 0
        N = len(sentence)
        buf = ''
        while x < N:
            y = route[x][1] + 1
            l_word = sentence[x:y]
            if self.re_eng.match(l_word) and len(l_word) == 1:
                buf += l_word
                x = y
            else:
                if buf:
                    yield buf
                    buf = ''
                yield l_word
                x = y
        if buf:
            yield buf
            buf = ''


    def refresh_dictionary(self):
        print('JieBaDictionary: Start Refresh Dictionary Observed Data Source By Database.')
        _older_v_size = len(self.vocabularies)
        
        # dictionary_list = CustomDictionaryWord.objects.values_list('pinyin', flat=True)
        # for d in dictionary_list:
        #     self.add_word(d)

        _freq_map = self.get_freq_map()

        _percent = 0

        sound_vocabularies = SoundVocabulary.objects.filter(status=1)
        _total = len(sound_vocabularies)
        _i = 0
        for sv in sound_vocabularies:
            _pinyin = sv.pinyin
            # _type = int(sv.type)
            _freq = _freq_map.get(_pinyin, 1)
            self.add_word(_pinyin, freq=_freq)

            if _i % 500 == 0:
                _percent = _i / _total * 100
                print(' {:.2f}%'.format(_percent), end="\r")
            _i += 1

        
        # new_vocabularies = NewVocabulary.objects.values_list('pinyin', flat=True)
        # for nv in new_vocabularies:
        #     self.add_word(nv)


        digital_vocabularies = DigitalVocabulary.objects.all()
        for dv in digital_vocabularies:
            digit = '{}_'.format(dv.digits)
            dv_pinyin = dv.pinyin
            self.add_word(digit)
            self.add_word(dv_pinyin)

        if len(self.vocabularies) > _older_v_size:
            self.save_vocabularies()
            print('Refreshed Vocabulary Last 10: ', self.vocabularies[-10:])
        
        print('FREQ Length: ', len(jieba.dt.FREQ), ', Vocabulary Length: ', len(self.vocabularies))
        # print(len(self.none_tone_map))

        return self


    def add_word(self, word, freq = None):
        if self.is_allowed_word(word):
            _is_new_word = self.is_new_word(word)
            _freq = int(freq) if freq else 1
            jieba.add_word(word, freq=_freq)

            if _is_new_word:
                self.vocabularies.append(word)
                self.vocabulary_freqs.append(_freq)
                self.add_none_tone_word(word)
            
            return True
        return False

    
    def add_none_tone_word(self, word):
        # if word.count(self.split_character) <= 4 and word[-2].isdigit():
        # if word.count(self.split_character) <= 4 and re.match(r'[\d]', word) == None:
        if word.count(self.split_character) <= 4:
            # _no_digit_word = re.sub(r'[\d]+', '', word)
            # _key = _no_digit_word.replace(self.split_character, '')
            _key = word.replace(self.split_character, '')

            words = self.none_tone_map.get(_key, [])
            if word not in words:
                words += [word]
                self.none_tone_map[_key] = words
                return True
        
        return False


    def get_none_tone_word(self, pinyin):
        # print('get_none_tone_word pinyin: ', pinyin)
        g_map = self.none_tone_map
        _pinyin = pinyin.replace(self.split_character, '')
        _basic = g_map.get(_pinyin, None)
        if _basic and len(_basic) == 1:
            return _basic
        # jing_yan_
        _buf = ''
        _tmp_words = []
        _i = 0
        _len = len(_pinyin)
        _words = []
        # merge single word
        while _i < _len:
            _p = _pinyin[_i]
            _buf += _p
            _basic = g_map.get(_buf, None)
            if _basic:
                _tmp_words = _basic
            else:
                if _tmp_words:
                    _words.append(_tmp_words)
                    _tmp_words = []
                    _buf = _p
            _i += 1
        
        _basic = g_map.get(_buf, None)
        if _basic:
            _words.append(_basic)
            # print('get_none_tone_word [] _words: ', _words)
            # merge sentence
            final_words = []
            _i = 0
            _len_words = len(_words)
            _vocabularies = self.vocabularies
            while _i < _len_words:
                _num_find_match = _i
                _ws = _words[_i]
                _next_i = _i +1
                for _w in _ws:
                    _merge_word = _w
                    while _next_i < _len_words:
                        _ws_next = _words[_next_i]
                        _is_find_next_match = False
                        for _w_n in _ws_next:
                            tmp_word = _merge_word + _w_n
                            # _matched = g_map.get(tmp_word, None)
                            _matched = tmp_word in _vocabularies
                            if _matched:
                                _is_find_next_match = True
                                _num_find_match = _next_i
                                _merge_word = tmp_word
                                break
                        
                        if _is_find_next_match:
                            _next_i += 1
                        else:
                            break
                    
                    if _num_find_match > _i:
                        # found match
                        final_words.append(_merge_word)
                        break
                
                if _num_find_match == _i:
                    final_words.append(_ws[0])
                else:
                    _i = _num_find_match
                
                _i += 1

            return final_words
        else:
            # print('word left _buf: ', _buf)
            # print('unknown none tone word _pinyin: ', _pinyin)
            return None


    def get_vocabulary(self, pure = False):
        if pure:
            return self.vocabularies
        else:
            return self.origin_vocabulary + self.vocabularies

    def get_unknown_position(self):
        return self.origin_vocabulary.index(self.unknown_character)

    def get_alphabet_position(self):
        return self.origin_vocabulary.index(self.alphabet_character)

    def get_reserve_position(self):
        return self.origin_vocabulary.index(self.reserve_character)

    
    def get_cut_for_search(self, sentence):
        return jieba.cut_for_search(sentence, HMM=False)


    def get_cut_all(self, sentence, min_length = 1):
        _dag = jieba.get_DAG(sentence)
        _n = len(sentence)
        result = []
        
        for _idx in range(_n):
            if _idx == 0 or sentence[_idx-1] == self.split_character:
                _dag_list = _dag[_idx]
                for __x in _dag_list:
                    _word = sentence[_idx:__x+1]
                    if _word.count(self.split_character) >= min_length:
                        result.append(_word)
            
        return result


    def get_DAG(self, sentence):
        return jieba.get_DAG(sentence)


    def get_freq_map(self):
        _json_data = self._jsonparser.load()
        res_map = {}
        for _ in _json_data:
            _pinyin = _[0]
            _freq_times = _[1]
            res_map[_pinyin] = _freq_times
        
        return res_map
    

    def is_new_word(self, _word):
        return _word not in self.vocabularies

    
    def is_allowed_word(self, _word):
        return len(_word) > 1 and _word[-1] == self.split_character

    
    def load_vocabularies(self, vocabulary=None):
        _list = []
        if isinstance(vocabulary, list) and len(vocabulary) >0:
            _list = vocabulary

            print('===========[load_vocabularies] by Vocabulary Data: ', vocabulary[-10:], len(vocabulary), flush=True)

        else:
            path = self.pickle_folder + '/tokenizer_vocabularies.pickle'
            if os.path.isfile(path):
                with open(path, 'rb') as handle:
                    _full_data = pickle.load(handle)
                    _list = _full_data[0]
                    # _voca_freqs = _full_data[1]
                
            else:
                self.save_vocabularies()

            print('===========[load_vocabularies] by Local File: ', _list[-10:], len(_list), flush=True)


        # if len(_list) != len(_voca_freqs):
        #     print('[ERROR] Vocabulary and Freqs Legnths Can Not Be Different', flush=True)
        #     exit(2)
        

        for _idx, _ in enumerate(_list):
            self.add_word(_, freq=_freq)
        
        # self.vocabularies = _list


    def save_vocabularies(self):
        _full_data = [self.vocabularies, self.vocabulary_freqs]
        with open(self.pickle_folder + '/tokenizer_vocabularies.bak', 'wb+') as handle:
            pickle.dump(_full_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        with open(self.pickle_folder + '/tokenizer_vocabularies.pickle', 'wb+') as handle:
            pickle.dump(_full_data, handle, protocol=pickle.HIGHEST_PROTOCOL)




class EnglishParser():
    """

    """
    _vocabularies = []
    _regex_english = r'[a-zA-Z]+'

    def __init__(self, vocabularies = []):

        if vocabularies:
            self.set_vocabulary(vocabularies)


    def set_vocabulary(self, vocabularies = []):
        if vocabularies:

            self._vocabularies = vocabularies

        else:

            self._vocabularies = self.get_vocabulary_by_database()
            print('[EnglishParser] Get Vocabulary On Database.')
            
        print('[EnglishParser][set_vocabulary] _vocabularies Length: ', len(self._vocabularies))

    
    def get_vocabulary(self):
        return self._vocabularies


    def get_vocabulary_by_database(self):
        _language = Language.objects.get(code='EN')
        _vocabulary = list(Vocabulary.objects.filter(language=_language).values_list('context', flat=True))
        return _vocabulary


    def replace_to_origin_english(self, text):

        
        
        new_text = re.sub(self._regex_english, self._sub_match_fn, text)
            
        # print('new_text: ', new_text)

        return new_text

    def _sub_match_fn(self, match):
        _diversity_suffix = ['ves', 'ies', 'es', 's', 'ing', 'ed']
        match_str = match.group()
        # print('match_str: ', match_str)
        if match_str not in self._vocabularies:
            for _dss in _diversity_suffix:
                _suffix = '{}$'.format(_dss)
                if re.findall(_suffix, match_str):
                    _fixed_str = re.sub(_suffix, '', match_str)
                    # print('_fixed_str: ', _fixed_str)

                    if _dss == 'ves':
                        _fixed_str_example = _fixed_str + 'f'
                        if _fixed_str_example in self._vocabularies:
                            return _fixed_str_example
                        _fixed_str_example = _fixed_str + 'fe'
                        if _fixed_str_example in self._vocabularies:
                            return _fixed_str_example

                    elif _dss == 'ies':
                        _fixed_str_example = _fixed_str + 'y'
                        if _fixed_str_example in self._vocabularies:
                            return _fixed_str_example

                    if _fixed_str in self._vocabularies:
                        return _fixed_str

        return match_str


    def parse_right_vocabulary_list(self, eng_str):
        result_list = []
        _eng_string = eng_str.strip()
        _eng_list = re.split(r'\s+', _eng_string)

        for _ in _eng_list:
            if re.match(self._regex_english, _):
                if _ not in self._vocabularies:
                    return []
                else:
                    result_list.append(_)
            else:
                return []

        return result_list

