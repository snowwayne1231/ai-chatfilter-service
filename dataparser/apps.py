from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig

from datetime import datetime
from .classes.map_hex import mapHexes
from .models import CustomDictionaryWord
from service.models import Blockword
from ai.models import SoundVocabulary, NewVocabulary
from ai.classes.translator_pinyin import translate_by_string

import xlrd
import os
import re
import jieba


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
                    
                    _next_child = [child[i] if i >= 0 else '' for i in _columns]
                    ary.append(_next_child)
        else:

            for rx in range(limit if limit > 0 else sh.nrows):

                child = [x.value for x in sh.row(rx)]
                ary.append(child)
        

        return ary



class MessageParser():

    regex_msg = re.compile("<msg>(.*)</msg>", re.IGNORECASE)
    regex_xml_lv = re.compile("<lv>(.*)</lv>", re.IGNORECASE)
    regex_xml_anchor = re.compile("<anchmsg>(.*)</anchmsg>", re.IGNORECASE)
    regex_xml_tag = re.compile("<[^>]+>[^<]*</[^>]+>")
    regex_bracket_lv = re.compile("\{viplv([^\}]*)\}", re.IGNORECASE)
    regex_bracket = re.compile("\{[^\}]*\}")

    def __init__(self):
        print('MessageParser init done.')

    
    def parse(self, string):
        lv = 0
        anchor = 0
        repres_msg = self.regex_msg.match(string)

        if repres_msg:
            text = repres_msg.group(1)
            repres_xml_lv = self.regex_xml_lv.search(text)
            if repres_xml_lv:
                lv = int(repres_xml_lv.group(1))

            repres_xml_anchor = self.regex_xml_anchor.search(text)
            if repres_xml_anchor:
                anchor = int(repres_xml_anchor.group(1))
            
            text = self.regex_xml_tag.sub("", text)
            
        else:
            text = string
            
            repres_bracket_lv = self.regex_bracket_lv.match(text)
            if repres_bracket_lv:
                lv = int(repres_bracket_lv.group(1))
            
            text = self.regex_bracket.sub("", text)

        text = self.translate_special_char(text)
        # text = self.split_word(text)

        return text, lv, anchor

    
    def translate_special_char(self, string):
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
            if _code >= 0x2000 and _code <= 0x206f: continue
            # 【3000-303F】 CJK Symbols and Punctuation 中日韓符號和標點  # 12290
            if _code >= 0x3000 and _code <= 0x303f: continue

            # if _code < 0x0020 or _code > 0x7e:
            if _code < 0x0030 or _code > 0x7a or (_code >= 0x3a and _code <= 0x40 ):
                continue
                # out of English or digits
                _hex16 = hex(_code)
                _string = mapHexes.get(_code, None)
                
                if _string:
                    _result += _string
                else:
                    # _result += uc
                    # print('out of char: ', _code, _hex16, uc, ' - ', _string)
                    pass
                
            else:
                _result += chr(_code).lower()
        
        return _result



class JieBaDictionary():
    """
        
    """
    split_character = '_'

    def __init__(self):
        jieba.re_eng = re.compile('[a-zA-Z0-9_]', re.U)
        dictionary_path = os.path.dirname(__file__) + '/assets/jieba.txt'
        jieba.initialize(dictionary=dictionary_path)
        self.refresh_dictionary()
        print('JieBaDictionary init done.')


    def split_word(self, text=''):
        _list = jieba.cut(text, HMM=False, cut_all=False) if text else []
        results = []
        _buf = ''
        
        for _ in _list:
            if not _:
                continue
            elif  _[-1] == self.split_character:
                results.append(_buf + _)
                _buf = ''
            else:
                _buf += _

        if _buf:
            print('why left _buf: ', _buf)
            print('text: ', text)
        
        return results


    def refresh_dictionary(self):
        
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

        sound_vocabularies = SoundVocabulary.objects.values_list('pinyin', flat=True)
        for sv in sound_vocabularies:
            if self.is_allowed_word(sv) and self.is_new_word(sv):
                jieba.add_word(sv)


        new_vocabularies = NewVocabulary.objects.values_list('pinyin', flat=True)
        for nv in new_vocabularies:
            if self.is_allowed_word(nv) and self.is_new_word(nv):
                jieba.add_word(nv)
        
        print('FREQ length: ', len(jieba.dt.FREQ))

        return self


    def is_new_word(self, _word):
        freq = jieba.get_FREQ(_word)
        _is_new = freq is None or freq == 0
        return _is_new

    
    def is_allowed_word(self, _word):
        return _word[-1] == self.split_character