from django.core.management.base import BaseCommand
from ai.train import train_pinyin as handle_train_pinyin
import os

class Command(BaseCommand):
    help = 'train models'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_excel_path', required=False,
            help='the path of excel file.',
        )
        parser.add_argument(
            '-a', dest='is_append_mode', required=False, action='store_true',
            help='is append to older data.',
        )

    def handle(self, *args, **options):
        path = options.get('input_excel_path', None)
        is_append_mode = options.get('is_append_mode', False)
    
        self.stdout.write('Handle AI training... ')

        if path:
            full_file_path = os.getcwd() + '/' + path
            self.stdout.write('Full input excel path: ' + full_file_path)
            handle_train_pinyin(full_file_path, is_append_mode)
        else:
            handle_train_pinyin()
        

        