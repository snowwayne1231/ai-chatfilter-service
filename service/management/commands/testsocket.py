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
        statuses = []

        if file_path:

            ep = ExcelParser(file=file_path)
            basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息', '发言内容'], ['状态', 'STATUS']]
            row_list = ep.get_row_list(column=basic_model_columns, limit=50000)
            for r in row_list:
                _loc = r[2]
                _status = int(r[3])
                if _loc:
                    messages.append(_loc)
                    statuses.append(_status)

        else:
            messages = ['hello','world','hi', 'hihi bady', '你好嗎我很好', '只要不贪心赢钱简单的，幑忪錝号真人之王', '死诈骗游戏']
            statuses = [0,0,0,0,0, 1, 4]

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        addr = (host, port)

        client.connect(addr)

        cmd_ints = [0x000001, 0x040001, 0x040002, 0x040003, 0x040004]

        num = 3
        command_hex = cmd_ints[num]

        keep_doing = True
        msgid = 0
        length_messages = len(messages)

        length_right = 0
        
        while keep_doing and msgid < length_messages:

            try:
                msgtxt = messages[msgid]
                status = statuses[msgid]

                if msgtxt:
                    # print('sending txt: ', msgtxt)
                    packed = pack(command_hex, msgid=msgid+100000000, msgtxt=msgtxt)

                    if msgid % 100 == 0:
                        print('{:2.1%}'.format(msgid / length_messages), end="\r")
                else:
                    print('msgtxt wrong: ', msgtxt)
                    continue
                
                client.send(packed)

                recv_data = client.recv(bufsize)
                if not recv_data:
                    print('not receive msgid: {}   msgtxt: {}'.format(msgid, msgtxt))
                    break

                # print('===== receive data =====')
                # print (recv_data.decode('utf-8'))
                trying_unpacked = unpack(recv_data)
                _is_deleted = trying_unpacked.code > 0
                if _is_deleted:
                    if status > 0:
                        length_right += 1
                else:
                    if status == 0:
                        length_right += 1
                # print('=========================')

                msgid += 1
                time.sleep(0.01)

            except KeyboardInterrupt:

                keep_doing = False


        print('disconnect from tcp server.')
        print('right ratio : {:2.2%}'.format(length_right / length_messages))
        client.close()

        