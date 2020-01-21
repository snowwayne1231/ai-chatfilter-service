from django.core.management.base import BaseCommand

from ai.predict import predict_by_pinyin
from dataparser.apps import ExcelParser
import os, json
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
        parser.add_argument(
            '-json', dest='output_json', required=False, action='store_true',
            help='whether output the result to json file.',
        )


    def handle(self, *args, **options):
        text = options.get('text', None)
        input_file = options.get('input_file', None)
        silence = options.get('silence', False)
        output_json = options.get('output_json', False)

        if text:

            self.stdout.write('Word of Prediction: ' + text)
            res = predict_by_pinyin(text, silence=silence, detail=True)
            self.stdout.write('Prediction is: ' + str(res))

        elif input_file:

            full_file_path = os.getcwd() + '/' + input_file
            self.stdout.write('Full input excel file path: ' + full_file_path)

            ep = ExcelParser(file=full_file_path)
            basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息'], ['STATUS', '審核結果']]
            row_list = ep.get_row_list(column=basic_model_columns)


            _status_list = [0,1,2,3,4,5,10,11,12,13,14,15]

            total_legnth = len(row_list)
            total_rights = 0
            total_rights_delete = 0
            total_right_map = {}
            total_wrong = 0
            total_missing_delete = 0
            total_mistake_delete = 0
            total_wrong_map = {}

            # mistake_delete = []
            # mistake_remain = []
            mistake_texts_map = {}

            room = 'local'

            try:

                for _s in _status_list:
                    total_right_map[_s] = 0
                    total_wrong_map[_s] = 0
                    mistake_texts_map[_s] = []

                _i = 0
                for row in row_list:
                    # room = row[0]
                    ans = int(row[3])
                    txt = row[2]
                    should_be_deleted = ans > 0
                    # print(txt)
                    predicted, processed_text = predict_by_pinyin(txt, room=room, silence=silence)
                    ai_delete = predicted > 0
                    # print(predicted)

                    if should_be_deleted == ai_delete:
                        total_rights += 1
                        total_right_map[predicted] += 1
                        if should_be_deleted:
                            total_rights_delete += 1
                    else:
                        total_wrong += 1
                        total_wrong_map[predicted] += 1

                        if should_be_deleted:
                            if ans == 5:
                                total_missing_delete += 1
                        else:
                            total_mistake_delete += 1

                        if ans != 5 and predicted == 0:
                            # is not deleted by other ai
                            pass

                        else:

                            # if should_be_deleted:
                            #     mistake_remain.append(txt)
                            # elif ai_delete:
                            #     mistake_delete.append(txt)
                                
                            # mistake_texts_map[predicted].append([txt, processed_text])
                            mistake_texts_map[predicted].append(txt)


                    _i += 1
                    if _i % 100 == 0:
                        
                        percent = _i / total_legnth
                        # self.stdout.write('%.2f\r' % percent)
                        # self.stdout.flush()
                        print("Progress of Prediction: {:2.1%}".format(percent), end="\r")
                        # gc.collect()

            except KeyboardInterrupt:
                print('KeyboardInterrupt Stop.')
            
            print('================== Prediction Result ==================')
            print('total_legnth: ', _i)
            print('total_rights: ', total_rights)
            print('total_rights_delete: ', total_rights_delete)
            # print(total_right_map)
            print('total_wrongs: ', total_wrong)
            print('total_missing_delete: ', total_missing_delete)
            print('total_mistake_delete: ', total_mistake_delete)
            # print(total_wrong_map)
            # print(total_wrong_answers)

            right_ratio = "{:2.2%}".format(total_rights /_i)
            print('right ratio: ', right_ratio)
            print('================== Prediction Details ==================')
            mistake_ratio_map = {}
            print('Mistake Ratios: ')
            for status, wrong_num in total_wrong_map.items():
                right_num = total_right_map[status]
                _sum = wrong_num + right_num
                if _sum == 0:
                    _ratio = 0
                else:
                    _ratio = wrong_num / _sum

                _percent = '{:2.2%}'.format(_ratio)
                mistake_ratio_map[status] = _percent
                print(' [{}] = {}   ::  {}/{}'.format(status, _percent, wrong_num, _sum))

            # print(mistake_texts_map)

            self.stdout.flush()

            if output_json:
                json_data = {
                    'ratio': right_ratio,
                    'num_rights': total_rights,
                    'num_wrongs': total_wrong,
                    'num_total': _i,
                    'ratio_right': total_rights / _i,
                    'ratio_wrong': total_wrong / _i,
                    'num_total_rights_delete': total_rights_delete,
                    'num_total_missing_delete': total_missing_delete,
                    'num_total_mistake_delete': total_mistake_delete,
                    'details': {
                        'total_wrong_map': total_wrong_map,
                        'mistake_ratio_map': mistake_ratio_map,
                        'mistake_texts_map': mistake_texts_map,
                    }
                }

                json_file_path = os.getcwd() + '/__prediction__.json'

                with open(json_file_path, 'w+', encoding = 'utf8') as handle:
                    json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
                    handle.write(json_string)
                
        else:
            
            self.stdout.write('Nothing happend.')

    
        

        

        
        

        