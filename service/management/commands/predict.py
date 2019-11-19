from django.core.management.base import BaseCommand

from ai.predict import predict_by_pinyin
from dataparser.apps import ExcelParser
import os

class Command(BaseCommand):
    help = 'predict text status possible'

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', dest='text', required=False,
            help='the text to be predicted.',
        )
        parser.add_argument(
            '-i', dest='input_file', required=False,
            help='the file of need to be predicted.',
        )


    def handle(self, *args, **options):
        text = options.get('text', None)
        input_file = options.get('input_file', None)

        if text:

            self.stdout.write('Word of Prediction: ' + text)
            res = predict_by_pinyin(text)
            self.stdout.write('Prediction is: ' + str(res))

        elif input_file:

            full_file_path = os.getcwd() + '/' + input_file
            self.stdout.write('Full input excel file path: ' + full_file_path)

            ep = ExcelParser(file=full_file_path)
            basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息'], ['STATUS', '審核結果']]
            row_list = ep.get_row_list(column=basic_model_columns)

            total_legnth = len(row_list)
            total_rights = 0
            total_right_map = {0:0, 1:0, 3:0, 5:0}
            total_wrong_predictions = {0:0, 1:0, 3:0, 5:0}
            total_wrong_answers = {0:0, 1:0, 3:0, 5:0}

            _i = 0
            for row in row_list:
                ans = int(row[3])
                txt = row[2]
                # print(txt)
                predicted = predict_by_pinyin(txt)
                # print(predicted)

                if ans == int(predicted):
                    total_rights += 1
                    total_right_map[ans] += 1
                else:
                    total_wrong_predictions[predicted] += 1
                    total_wrong_answers[ans] += 1

                _i += 1
                if _i % 200 == 0:
                    
                    percent = _i / total_legnth
                    # self.stdout.write('%.2f\r' % percent)
                    # self.stdout.flush()
                    print("Progress of Prediction: {:2.1%}".format(percent), end="\r")
            

            print('========= Prediction Result =========')
            print('total_legnth: ', total_legnth)
            print('total_rights: ', total_rights)
            print(total_right_map)
            print('total_wrongs: ', total_legnth - total_rights)
            print(total_wrong_predictions)
            print(total_wrong_answers)
            self.stdout.flush()
        else:
            
            self.stdout.write('Nothing happend.')

    
        

        

        
        

        