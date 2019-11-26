from django.core.management.base import BaseCommand

from ai.predict import predict_by_pinyin
from dataparser.apps import ExcelParser
import os
# import gc


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
        parser.add_argument(
            '-s', dest='silence', required=False, action='store_true',
            help='silence mode.',
        )


    def handle(self, *args, **options):
        text = options.get('text', None)
        input_file = options.get('input_file', None)
        silence = options.get('silence', False)

        if text:

            self.stdout.write('Word of Prediction: ' + text)
            res = predict_by_pinyin(text, silence=silence)
            self.stdout.write('Prediction is: ' + str(res))

        elif input_file:

            full_file_path = os.getcwd() + '/' + input_file
            self.stdout.write('Full input excel file path: ' + full_file_path)

            ep = ExcelParser(file=full_file_path)
            basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息'], ['STATUS', '審核結果']]
            row_list = ep.get_row_list(column=basic_model_columns)

            total_legnth = len(row_list)
            total_rights = 0
            _status_list = [0,1,3,5,10,11,12,13,14,15]
            total_right_map = {}
            total_wrong_predictions = {}
            total_wrong_answers = {}

            # mistake_delete = []
            # miss_delete = []

            try:

                for _s in _status_list:
                    total_right_map[_s] = 0
                    total_wrong_predictions[_s] = 0
                    total_wrong_answers[_s] = 0

                _i = 0
                for row in row_list:
                    room = row[0]
                    ans = int(row[3])
                    txt = row[2]
                    should_be_deleted = ans > 0
                    # print(txt)
                    predicted = predict_by_pinyin(txt, room=room, silence=silence)
                    ai_delete = predicted > 0
                    # print(predicted)

                    if should_be_deleted == ai_delete:
                        total_rights += 1
                        total_right_map[predicted] += 1
                    else:
                        total_wrong_predictions[predicted] += 1
                        total_wrong_answers[ans] += 1

                        # if should_be_deleted:
                        #     miss_delete.append(txt)
                        # elif ai_delete:
                        #     mistake_delete.append(txt)


                    _i += 1
                    if _i % 200 == 0:
                        
                        percent = _i / total_legnth
                        # self.stdout.write('%.2f\r' % percent)
                        # self.stdout.flush()
                        print("Progress of Prediction: {:2.1%}".format(percent), end="\r")
                        # gc.collect()

            except KeyboardInterrupt:
                print('KeyboardInterrupt Stop.')
            

            print('========= Prediction Result =========')
            print('total_legnth: ', _i)
            print('total_rights: ', total_rights)
            print(total_right_map)
            print('total_wrongs: ', _i - total_rights)
            print(total_wrong_predictions)
            # print(total_wrong_answers)

            right_ratio = "{:2.1%}".format(total_rights /_i)
            print('right ratio: ', right_ratio, end="%")
            # print('========= Prediction Details =========')
            # print('Miss:')
            # print(miss_delete)
            # print('Mistake delete:')
            # print(mistake_delete)
            self.stdout.flush()
        else:
            
            self.stdout.write('Nothing happend.')

    
        

        

        
        

        