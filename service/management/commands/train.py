from django.core.management.base import BaseCommand
from ai.train import train_pinyin as handle_train_pinyin, load_data
import os

class Command(BaseCommand):
    help = 'train models'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_excel_path', required=False,
            help='the path of excel file.',
        )

    def handle(self, *args, **options):
        path = options.get('input_excel_path', None)
    
        self.stdout.write('Handle AI training... ')

        if path:
            full_file_path = os.getcwd() + '/' + path
            self.stdout.write('Full input excel path: ' + full_file_path)
            handle_train_pinyin(full_file_path)
        else:
            handle_train_pinyin()
        

        