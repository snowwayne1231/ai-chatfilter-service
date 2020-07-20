from django.core.management.base import BaseCommand
from django.apps import apps
from dataparser.apps import ExcelParser, MessageParser
from dataparser.jsonparser import JsonParser
import os, json

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
            _filename = 'output.json'
            output_path = os.path.join(_dirname, _filename)

        try:
            _ep = ExcelParser(file=input_file)
            _basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息', '禁言内容', '发言内容'], ['STATUS', '審核結果', '状态']]
            result_list = _ep.get_row_list(column=_basic_model_columns)


            _message_parser = MessageParser()
            for res in result_list:
                msg = res[2]
                text, lv, anchor = _message_parser.parse(msg)

                res.append(text)
                res.append(lv)
                res.append(anchor)

            print('result_list length: ', len(result_list))
            print('output_path: ', output_path)

            _jp = JsonParser(file=output_path)
            _jp.save(result_list)
            
        except Exception as err:
            print(err)


        