from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys, getopt, re
import xlrd

from datetime import datetime

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



if __name__ == '__main__':
    ep = ExcelParser(file=os.getcwd()+'/../_datas')
    basic_model_columns = [['MESSAGE', '聊天信息', '禁言内容', '发言内容'], ['STATUS', '審核結果', '状态']]
    result_list = ep.get_row_list(column=basic_model_columns)
    not_english_regxp = re.compile('[^a-z]+')
    space_regxp = re.compile('[\s]+')

    res_set = {}
    result = []
    for _ in result_list:
        _loc = _[0].lower()
        _loc = re.sub(not_english_regxp, ' ', _loc)
        _list = re.split(space_regxp, _loc)
        for _eng in _list:
            _next = res_set.get(_eng, 0)
            _next += 1
            res_set[_eng] = _next
            if _eng not in result:
                result.append(_eng)

    result_list = []
    

    for _ in sorted(result):
        _i = res_set[_]
        if _i > 2:
            result_list.append(_)

    file_object = open(os.path.dirname(__file__)+'/__english_list__.json', 'w', encoding='utf8')
    output_str = '\r'.join(result_list)
    file_object.write(output_str)
    file_object.close()
    