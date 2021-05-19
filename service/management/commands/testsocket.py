from django.core.management.base import BaseCommand
from configparser import RawConfigParser

from tcpsocket.chat_package import pack, unpack
from dataparser.apps import ExcelParser

import os, sys, socket, time, threading


threadLimiter = threading.BoundedSemaphore(8)
class AutoReleaseThread(threading.Thread):

    def run(self):
        threadLimiter.acquire()
        try:
            self.Executemycode()
        finally:
            threadLimiter.release()

    def Executemycode(self):
        print(" Hello World!")
        # <your code here>


class Command(BaseCommand):
    help = 'train models'
    client = None
    bufsize = 1024
    spend_recv_second = 0

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
        parser.add_argument(
            '-m', dest='multiple', required=False, help='use multiple thread to test.',
        )

    def handle_recv_data(self, packed, status):
        _start_time = time.time()
        self.client.send(packed)
        try:
            recv_data = self.client.recv(self.bufsize)
            _recv_time = time.time()
            _spend_recv_second = _recv_time - _start_time
            self.spend_recv_second += _spend_recv_second
        except socket.timeout:
            print('Recv Data Timeout.')
            return 0
        except Exception:
            recv_data = None

        if not recv_data:
            print('not receive packed: {} '.format(packed))
            return 0
        _trying_unpacked = unpack(recv_data)
        _is_deleted = _trying_unpacked.code > 0
        _is_right = False
        if _is_deleted:
            if status > 0:
                _is_right = True
        else:
            if status == 0:
                _is_right = True
        
        if _is_right:
            return 1
        else:
            print('Wrong Predict :: txt = [{}]   ans = [{}]'.format(_trying_unpacked.code, status))
            return 0


    def handle(self, *args, **options):
        _handle_start_time = time.time()
        file_path = options.get('input_excel_path', None)
        port = options.get('port')
        host = options.get('host')
        is_multiple = options.get('multiple', False)

        if port is None:
            port = 8025
        else:
            port = int(port)
            
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

        client.settimeout(3)
        
        # client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
        addr = (host, port)

        client.connect(addr)
        
        self.client = client

        cmd_ints = [0x000001, 0x040001, 0x040002, 0x040003, 0x040004]

        num = 3
        command_hex = cmd_ints[num]

        keep_doing = True
        msgid = 0
        length_messages = len(messages)

        length_right = 0
        _threads = []
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
                
                

                if is_multiple:
                    _new_thread = threading.Thread(target= self.handle_recv_data, args = (packed, status))
                    _threads.append(_new_thread)
                    _new_thread.start()
                else:
                    length_right += self.handle_recv_data(packed, status)
                    
                time.sleep(0.001)
                msgid += 1

            except KeyboardInterrupt:

                keep_doing = False

        
        for t in _threads:
            t.join()
        print('disconnect from tcp server.')
        print('Length Of Message: ', length_messages, 'Count Of Threading: ', threading.active_count())
        print('Spend Receive Second: ', self.spend_recv_second, 'Execute Time: ', time.time() - _handle_start_time)
        print('right ratio : {:2.2%}'.format(length_right / length_messages))
        client.close()

