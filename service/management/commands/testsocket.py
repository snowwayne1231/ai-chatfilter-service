from django.core.management.base import BaseCommand
import os, sys, getopt, socket, time
from configparser import RawConfigParser

from tcpsocket.chat_package import pack, unpack
from dataparser.apps import ExcelParser

class Command(BaseCommand):
    help = 'train models'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i', dest='input_excel_path', required=False, help='the path of excel file.',
        )
        parser.add_argument(
            '-port', dest='port', required=False, help='port',
        )
        parser.add_argument(
            '-host', dest='host', required=False, help='host',
        )

    def handle(self, *args, **options):
        file_path = options.get('input_excel_path', None)
        port = options.get('port')
        host = options.get('host')
        bufsize = 1024

        if port is None:
            port = 8025
        if host is None:
            host = '127.0.0.1'

        messages = []

        if file_path:

            ep = ExcelParser(file=file_path)
            basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息']]
            row_list = ep.get_row_list(column=basic_model_columns, limit=5000)
            for r in row_list:
                _loc = r[2]
                if _loc:
                    messages.append(_loc)

        else:
            messages = ['q1','w2','e3']

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    
        addr = (host, port)

        client.connect(addr)

        cmd_ints = [0x000001, 0x040001, 0x040002, 0x040003, 0x040004]

        num = 3
        command_hex = cmd_ints[num]

        keep_doing = True
        msgid = 0
        length_messages = len(messages)
        
        while keep_doing and msgid < length_messages:

            try:
                msgtxt = messages[msgid]

                if msgtxt:
                    print('sending txt: ', msgtxt)
                    packed = pack(command_hex, msgid=msgid+1, msgtxt=msgtxt)
                else:
                    break
                
                client.send(packed)

                recv_data = client.recv(bufsize)
                if not recv_data:
                    break

                # print('===== receive data =====')
                # print (recv_data.decode('utf-8'))
                trying_unpacked = unpack(recv_data)
                
                # print(trying_unpacked)
                # print('=========================')

                msgid += 1
                time.sleep(0.2)

            except KeyboardInterrupt:

                keep_doing = False


        print('disconnect from tcp server.')
        client.close()

        