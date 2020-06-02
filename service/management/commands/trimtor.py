from django.core.management.base import BaseCommand
from dataparser.apps import ExcelParser, MessageParser
import os

class Command(BaseCommand):
    help = 'trim excel editor'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_excel_path', required=True,
            help='the path of excel file.',
        )
        parser.add_argument(
            '-o', dest='output_path', required=False,
            help='the path of output data.',
        )
        # parser.add_argument(
        #     '-f', dest='final_accuracy', required=False, type=float,
        #     help='set should be stoped accuracy ratio.',
        # )
        # parser.add_argument(
        #     '-t', dest='time', required=False, type=int,
        #     help='how many time to spend.',
        # )
        # parser.add_argument(
        #     '-grm', dest='grammar_mode', required=False, action='store_true',
        #     help='whether grammar mode is on.',
        # )

    def handle(self, *args, **options):
        path = options.get('input_excel_path', None)
        path_output = options.get('output_path', None)

        
        _full_file_path = os.getcwd() + '/' + path
        self.stdout.write('Excel Path: ' + _full_file_path)

        _ep = ExcelParser(file=_full_file_path)
        _mp = MessageParser()


        if path_output:
            _full_output_path = os.getcwd() + '/' + path_output
        else:
            _full_output_path = os.getcwd() + '/trimtor.output.xlsx'
        

        _list = _ep.get_row_list(column=[['发言内容'], ['状态']])

        print('Origin Length: ', len(_list))
        _result_list = []

        for row in _list:
            msg = row[0]
            text, lv, anchor = _mp.parse(msg)
            text = text.replace(' ', '')

            if text and len(text)>0 and anchor == 0:
                _result_list.append(row)
            # else:
            #     print('Trimed Text: ', text, 'Origin Msg: ', msg)
        
        print('After Length: ', len(_result_list))

        _ep.export_excel(file=_full_output_path, data=_result_list)
            
        

        