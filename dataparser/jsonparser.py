from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig
from datetime import datetime

import os
import re
import json
import pickle


class JsonParser():
    """
        get_row_list (column=[], limit=0)
        return List
    """
    file = None
    data = {}
    is_multiple = False
    file_extension = re.compile("^(.*).json?$", re.IGNORECASE)

    def __init__(self, **kwargs):

        self.file = kwargs.get(
            'file',
            None,
        )

        if self.file:
            start_time = datetime.now()

            if os.path.isdir(self.file):

                self.is_multiple = True
                _total_data = []

                for _file in os.listdir(self.file):

                    if self.file_extension.search(_file):

                        _file_path = '{}/{}'.format(self.file, _file)
                        _data = self.load(_file_path)
                        _total_data += _data
                
                self.data = _total_data

            else:

                self.is_multiple = False
                # self.load()
                

            end_time = datetime.now()
            spend_second = (end_time - start_time).total_seconds()

            print('====ExcelParser Loads File spend seconds: ', spend_second)

        else:
            
            print('JsonParser Failed With Wrong File path.')


    def get_data(self):
        return self.data


    def load(self, path = None):
        _file = self.file if path is None else path
        _data = None

        try:

            if os.path.isfile(_file):

                with open(_file, 'r+', encoding='utf-8') as f:
                    _data = json.loads(f.read())
                    self.data = _data

        except Exception as err:

            print('[JsonParser][load] Error', err)

        return _data


    def save(self, data = None):
        _file = self.file

        try:

            # if not os.path.isfile(_file):

            if data is None:
                data = self.data
            else:
                self.data = data

            with open(_file, 'w+', encoding='utf-8') as f:
                # print('data: ', data[:10])
                json.dump(data, f, ensure_ascii=False, indent=1)

        except Exception as err:

            print('[JsonParser][save] Error', err)

        return self
        
        
