from django.core.management.base import BaseCommand
from ai.train import train_pinyin_by_json_path, train_grammar_by_json_path, train_english_by_json_path
import os

class Command(BaseCommand):
    help = 'train models'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_excel_path', required=False,
            help='the path of excel file.',
        )
        parser.add_argument(
            '-f', dest='final_accuracy', required=False, type=float,
            help='set should be stoped accuracy ratio.',
        )
        parser.add_argument(
            '-t', dest='time', required=False, type=int,
            help='how many time to spend.',
        )
        parser.add_argument(
            '-grm', dest='grammar_mode', required=False, action='store_true',
            help='whether grammar mode is on.',
        )
        parser.add_argument(
            '-eng', dest='english_mode', required=False, action='store_true',
            help='whether engilsh mode is on.',
        )


    def handle(self, *args, **options):
        path = options.get('input_excel_path', None)
        final_accuracy = options.get('final_accuracy', None)
        grammar_mode = options.get('grammar_mode', False)
        english_mode = options.get('english_mode', False)
        max_spend_time = options.get('time', 0)
    
        self.stdout.write('Handle AI training... ')

        if path:
            full_file_path = os.getcwd() + '/' + path
            self.stdout.write('Full input excel path: ' + full_file_path)
            if grammar_mode:
                train_grammar_by_json_path(full_file_path, final_accuracy=final_accuracy, max_spend_time=max_spend_time)
            elif english_mode:
                train_english_by_json_path(full_file_path, final_accuracy=final_accuracy, max_spend_time=max_spend_time)
            else:
                train_pinyin_by_json_path(full_file_path, final_accuracy=final_accuracy, max_spend_time=max_spend_time)
        else:
            print('No File Path Input.')
        

        