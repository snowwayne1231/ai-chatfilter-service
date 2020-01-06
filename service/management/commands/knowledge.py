from django.core.management.base import BaseCommand
from ai.knowledge.main import KnowledgeCenter
import os

class Command(BaseCommand):
    help = "knowledge, to know how about words"

    def add_arguments(self, parser):
        parser.add_argument('-i', dest='file', type=str, help="the file path of need")

    def handle(self, *args, **options):
        _file = options.get('file', '')

        if _file:
            _full_file_path = os.getcwd() + '/' + _file
            kc = KnowledgeCenter()
            kc.absorb_dictionary(_full_file_path)
        
    

        