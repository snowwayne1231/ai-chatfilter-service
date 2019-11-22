from django.core.management.base import BaseCommand
from pypinyin import pinyin, Style
import os

class Command(BaseCommand):
    help = "tracing pinyin for text."

    def add_arguments(self, parser):
        parser.add_argument('-t', dest='text', type=str, help="text")

    def handle(self, *args, **options):
        _text = options.get('text', '')
        self.stdout.write('tracing pinyin :: ' + _text)
        _words = pinyin(_text, strict=False, style=Style.NORMAL, heteronym=True)
        print('pinyin words: ', _words)
    

        