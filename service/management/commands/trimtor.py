from django.core.management.base import BaseCommand
from dataparser.apps import ExcelParser
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
        path_output = options.get('output_path', False)

        
        _full_file_path = os.getcwd() + '/' + path
        self.stdout.write('Excel Path: ' + _full_file_path)

        _ep = ExcelParser(file=_full_file_path)


        if path_output:
            
        else:
            
        

        