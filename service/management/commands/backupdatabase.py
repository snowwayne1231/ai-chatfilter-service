from django.core.management.base import BaseCommand
from django.apps import apps
import os, time
from datetime import datetime

class Command(BaseCommand):
    help = "backup data in database."

    # def add_arguments(self, parser):
        # parser.add_argument(
        #     '-m', dest='model_name', required=True,
        #     help='the name of model.',
        # )
        # parser.add_argument(
        #     '-a', dest='app_name', required=False,
        #     help='the name of app.',
        # )

    def handle(self, *args, **options):
        _st_time = datetime.now()
        # model_name = options.get('model_name', None)
        # app_name = options.get('app_name', 'service')
        ModelGoodSentence = apps.get_model(app_label='service', model_name='GoodSentence')
        _first_row = ModelGoodSentence.objects.first()

        _table_name = ModelGoodSentence._meta.db_table
        _st_date = (str(_first_row.date).split(' ')[0]).replace('-', '_')
        _end_date = (str(_st_time).split(' ')[0]).replace('-', '_')

        _new_table_name = '{}_{}_to_{}'.format(_table_name, _st_date, _end_date)
        
        print("New Table Name: ", _new_table_name)
        ModelGoodSentence.objects.raw('ALTER TABLE {} RENAME TO {};'.format(_table_name, _new_table_name))
        ModelGoodSentence.objects.raw('CREATE TABLE {} AS TABLE {} WITH NO DATA;'.format(_table_name, _new_table_name))
        print('Done Rename Talbe [{}] & [{}]'.format(_table_name, _new_table_name))

        _ed_time = datetime.now()
        print('Gap: ', _ed_time - _st_time)


        