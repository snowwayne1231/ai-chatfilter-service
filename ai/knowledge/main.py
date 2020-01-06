from ai.models import Vocabulary
from dataparser.apps import ExcelParser

class KnowledgeCenter():

    def __init__(self):
        pass

    def absorb_dictionary(self, file_path):
        ep = ExcelParser(file=file_path)
        rows = ep.get_row_list(column=['字詞名', '漢語拼音', '釋義'], limit=400)
        print(rows)
        