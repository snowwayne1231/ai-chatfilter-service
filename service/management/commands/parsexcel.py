from django.core.management.base import BaseCommand
from django.apps import apps
from dataparser.apps import ExcelParser, MessageParser
from dataparser.jsonparser import JsonParser
from ai.classes.translator_pinyin import translate_by_string
import os, json, re
from datetime import date

class Command(BaseCommand):
    help = "parse the excel file to json data."

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_file', required=True,
            help='the path of excel file.',
        )
        parser.add_argument(
            '-o', dest='output_path', required=False,
            help='the name of app.',
        )

    def handle(self, *args, **options):
        input_file = options.get('input_file')
        output_path = options.get('output_path', None)

        if output_path is None:
            _dirname = os.path.dirname(input_file)
            _filename = '{}.json'.format(date.today())
            output_path = os.path.join(_dirname, _filename)

        try:
            _ep = ExcelParser(file=input_file)
            _basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息', '禁言内容', '发言内容'], ['STATUS', '審核結果', '状态']]
            _excel_data = _ep.get_row_list(column=_basic_model_columns)
            _idx = 0
            _checking_map = {}
            _has_duplicate = False
            result_list = []

            _message_parser = MessageParser()

            _excel_data.reverse()
            for _data in _excel_data:
                msg = _data[2]
                status = int(_data[3])
                is_deleted = status > 0 if status else False
                text, lv, anchor = _message_parser.parse(msg)

                _data.append(text)
                _data.append(lv)
                _data.append(anchor)

                if anchor == 0:
                    _pinyin_text = ''.join(translate_by_string(text)).replace('_', '')
                    # print('_pinyin_text: ', _pinyin_text)
                    if len(_pinyin_text) == 1:
                        _pinyin_text = '_'
                    else:
                        _pinyin_text = re.sub(r'\d+', '_', _pinyin_text)
                    
                    _check = _checking_map.get(_pinyin_text, None)
                    if _check:
                        _check_is_deleted = _check[2] > 0
                        if _check_is_deleted != is_deleted:
                            continue
                            # _has_duplicate = True
                            # _against_idx = _check[0]
                            # _against_msg = _check[1]
                            # print('Duplicate MSG [{}], idx: {} || against idx: {}, msg: [{}]'.format(msg, _idx, _against_idx, _against_msg))
                        
                    else:
                        
                        _checking_map[_pinyin_text] = [_idx, msg, is_deleted]

                    result_list.append(_data)

                _idx += 1

            if _has_duplicate:

                print('Stop.')

            else: 
                print('_excel_data length: ', len(_excel_data))
                print('result_list length: ', len(result_list))
                print('output_path: ', output_path)

                _jp = JsonParser(file=output_path)
                _jp.save(result_list)
            
        except Exception as err:
            print(err)


        