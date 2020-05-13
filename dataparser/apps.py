from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig

from datetime import datetime
from .classes.map_hex import mapHexes
from .models import CustomDictionaryWord
from service.models import Blockword
from ai.models import SoundVocabulary, NewVocabulary, DigitalVocabulary
from ai.classes.translator_pinyin import translate_by_string

import xlrd
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
        for book in self.books:

            if just_first_sheet:
                sheet = book.sheet_by_index(0)
                rows = self.get_row_list_by_sheet(sheet, column=column, limit=limit)
                total_rows += rows

        return total_rows
    
    def get_row_list_by_sheet(self, sheet, column=[], limit=0):
        sh = sheet
        print("==Getting Data in Sheet name: {0}, rows: {1}, cols:{2}".format(sh.name, sh.nrows, sh.ncols))
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
    unknown_character = '#UNKNOW#'
    pad_character = '#PAD#'
    number_character = '#NUM#'
    folder = os.path.dirname(__file__)
    pickle_folder = os.path.dirname(__file__) + '/_pickles'
    vocabularies = []
    none_tone_map = {}

    def __init__(self, vocabulary=[]):
        jieba.re_eng = re.compile('[a-zA-Z0-9_]', re.U)
        jieba.initialize(dictionary=self.folder + '/assets/jieba.txt')

        if not os.path.isdir(self.pickle_folder):
            os.mkdir(self.pickle_folder)

        if len(vocabulary) == 0:
            self.load_vocabularies()
            self.refresh_dictionary()
        else:
            self.load_vocabularies(vocabulary)
            self.save_vocabularies()
        
        
        print('JieBaDictionary Initial Done.')


    def split_word(self, text=''):
        _list = jieba.cut(text, HMM=False, cut_all=False) if text else []
        results = []
        unknowns = []
        _buf = ''
        
        for _ in _list:
            print('split_word single _: ', _)
            if not _:
                continue
            elif  _[-1] == self.split_character:

                if _buf:
                    __ = _buf + _
                    _buf = ''
                    if __[:-1].isdigit():
                        print('[split_word] number_character 111 __: ', __)
                        results.append(self.number_character)
                        continue

                    _none_tone_words = self.get_none_tone_word(__)
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
                            print('[split_word] number_character 222 __: ', __)
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
        
        print('[split_word] origin text: ', text)
        
        print('[split_word] results: ', results)
        print('[split_word] unknowns: ', unknowns)
        return results, unknowns


    def refresh_dictionary(self):
        print('JieBaDictionary: Start Refresh Dictionary.')
        _older_v_size = len(self.vocabularies)
        
        # dictionary_list = CustomDictionaryWord.objects.all()
        # for d in dictionary_list:
        #     text = d.text
        #     jieba.add_word(text)
        #     jieba.add_word(translate_by_string(text))

        # blockwords = Blockword.objects.all()
        # for b in blockwords:
        #     text = b.text 
        #     jieba.add_word(text)
        #     jieba.add_word(translate_by_string(text))

        _percent = 0

        sound_vocabularies = SoundVocabulary.objects.values_list('pinyin', flat=True)
        _total = len(sound_vocabularies)
        _i = 0
        for sv in sound_vocabularies:
            self.add_word(sv)

            if _i % 500 == 0:
                _percent = _i / _total * 100
                print(' {:.2f}%'.format(_percent), end="\r")
            _i += 1
        
        # print([_[1] for _ in self.none_tone_map.items()if len(_[1]) > 1])
        # exit(2)
        
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
        
        print('FREQ length: ', len(jieba.dt.FREQ), ', Vocabulary: ', len(self.vocabularies))
        # print(len(self.none_tone_map))

        return self


    def add_word(self, word):
        if self.is_allowed_word(word) and self.is_new_word(word):
            jieba.add_word(word)
            self.vocabularies.append(word)
            self.add_none_tone_word(word)
            
            return True
        return False

    
    def add_none_tone_word(self, word):
        # if word.count(self.split_character) <= 4 and word[-2].isdigit():
        if word.count(self.split_character) <= 4 and re.match(r'[\d]', word) == None:
            _no_digit_word = re.sub(r'[\d]+', '', word)
            
            _key = _no_digit_word.replace(self.split_character, '')
            # _key = _no_digit_word

            words = self.none_tone_map.get(_key, [])
            if word not in words:
                words += [word]
                self.none_tone_map[_key] = words
                return True
        
        return False


    def add_vocabulary(self, words):
        count = 0
        # should_be_insertd = []
        for w in words:
            if self.add_word(w):
                count += 1
                # should_be_insertd.append(w)
        if count > 0:
            self.save_vocabularies()

        return count


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
            return [self.pad_character, self.unknown_character, self.number_character, '#reserve#'] + self.vocabularies

    def get_unknown_position(self):
        return self.get_vocabulary().index(self.unknown_character)

    def is_new_word(self, _word):
        return _word not in self.vocabularies

    
    def is_allowed_word(self, _word):
        return len(_word) > 1 and _word[-1] == self.split_character

    
    def load_vocabularies(self, vocabulary=None):
        _list = []
        if isinstance(vocabulary, list) and len(vocabulary) >0:
            _list = vocabulary
        else:
            path = self.pickle_folder + '/tokenizer_vocabularies.pickle'
            if os.path.isfile(path):
                with open(path, 'rb') as handle:
                    _list = pickle.load(handle)
            else:
                self.save_vocabularies()

        for _ in _list:
            jieba.add_word(_)
            self.add_none_tone_word(_)
        
        self.vocabularies = _list


    def save_vocabularies(self):
        with open(self.pickle_folder + '/tokenizer_vocabularies.bak', 'wb+') as handle:
            pickle.dump(self.vocabularies, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        with open(self.pickle_folder + '/tokenizer_vocabularies.pickle', 'wb+') as handle:
            pickle.dump(self.vocabularies, handle, protocol=pickle.HIGHEST_PROTOCOL)

