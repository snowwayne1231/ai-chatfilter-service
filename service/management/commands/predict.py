from django.core.management.base import BaseCommand

from ai.predict import predict_by_pinyin
import os

class Command(BaseCommand):
    help = 'predict text status possible'

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', dest='text', required=True,
            help='the text to be predicted.',
        )

    def handle(self, *args, **options):
        text = options.get('text', None)
    
        self.stdout.write('Word of Prediction: ' + text)

        res = predict_by_pinyin(text)

        
        

        