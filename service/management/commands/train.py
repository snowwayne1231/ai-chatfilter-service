from django.core.management.base import BaseCommand
from ai.train import train_pinyin as handle_train_pinyin
import os

class Command(BaseCommand):
    help = 'train models'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_path', required=True,
            help='the path of excel file.',
        )

    def handle(self, *args, **options):
        path = options['input_path']
        # self.stdout.write(path)
        full_file_path = os.getcwd() + '/' + path
        self.stdout.write('Full input excel path: ' + full_file_path)
        self.stdout.write('Handle AI training... ')
        handle_train_pinyin(full_file_path)
        