from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, connections
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
        ModelBlockedSentence = apps.get_model(app_label='service', model_name='BlockedSentence')
        _first_row = ModelGoodSentence.objects.first()

        if not _first_row:
            print('Nothing To Backup.')
            exit(2)

        _table_name = ModelGoodSentence._meta.db_table
        _table_name_blocked = ModelBlockedSentence._meta.db_table
        _st_date = (str(_first_row.date).split(' ')[0]).replace('-', '_')
        _end_date = (str(_st_time).split(' ')[0]).replace('-', '_')

        _new_table_name = '{}_{}_to_{}'.format(_table_name, _st_date, _end_date)
        _new_table_name_blocked = '{}_{}_to_{}'.format(_table_name_blocked, _st_date, _end_date)
        
        print("New Table Name: ", _new_table_name)
        _sql_rename_table = 'ALTER TABLE {} RENAME TO {};'.format(_table_name, _new_table_name)
        _sql_rename_table_2 = 'ALTER TABLE {} RENAME TO {};'.format(_table_name_blocked, _new_table_name_blocked)
        _sql_create_new_table = 'CREATE TABLE {} AS SELECT * FROM {} WHERE FALSE;'.format(_table_name, _new_table_name)
        _sql_create_new_table_2 = 'CREATE TABLE {} AS SELECT * FROM {} WHERE FALSE;'.format(_table_name_blocked, _new_table_name_blocked)
        
        # print('SQL1 : {}'.format(_sql_rename_table))
        # print('SQL2 : {}'.format(_sql_create_new_table))
        
        connection = connections[DEFAULT_DB_ALIAS]
        
        with connection.cursor() as cursor:
            if _st_date == _end_date:
                cursor.execute('DROP TABLE IF EXISTS {};'.format(_new_table_name))
                cursor.execute('DROP TABLE IF EXISTS {};'.format(_new_table_name_blocked))
            
            cursor.execute(_sql_rename_table)
            cursor.execute(_sql_create_new_table)
            cursor.execute(_sql_rename_table_2)
            cursor.execute(_sql_create_new_table_2)

        print('Done Rename Table [{}] ==> [{}]'.format(_table_name, _new_table_name))
        print('Done Rename Table [{}] ==> [{}]'.format(_table_name_blocked, _new_table_name_blocked))
        _ed_time = datetime.now()
        print('Spend Time: ', _ed_time - _st_time)


        