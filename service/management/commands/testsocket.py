import logging
from django.core.management.base import BaseCommand
from configparser import RawConfigParser

from tcpsocket.chat_package import pack, unpack
from dataparser.apps import ExcelParser

import os, sys, socket, time, threading

BIAS_MSGID = 100000000
MAX_TIMEOUT_TIMES = 3

class Command(BaseCommand):
    help = 'train models'
    client = None
    bufsize = 1024
    spend_recv_second = 0
    length_right = 0
    length_timeout_no_recv = 0
    timeout_times = 0

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
        parser.add_argument(
            '-gap', dest='time_gap', required=False, help='set time gap for every 8 records.',
        )

    def while_recv_data(self, statuses, messages):
        _total_length = len(statuses)
        while _total_length > 0:
            try:
                _start_time = time.time()
                recv_data = self.client.recv(self.bufsize)
                _recv_time = time.time()
                _spend_recv_second = _recv_time - _start_time
                self.spend_recv_second += _spend_recv_second
                while recv_data:
                    _total_length -= 1
                    recv_data = self.handle_recv_data(recv_data, statuses, messages)
            except socket.timeout:
                # print('Recv Data Timeout. txt: {}'.format(messages[msgidx]))
                self.length_timeout_no_recv += 1
                logging.warning('Recv Timeout Length: {}'.format(self.length_timeout_no_recv))
                if self.length_timeout_no_recv >= MAX_TIMEOUT_TIMES:
                    self.length_timeout_no_recv = _total_length
                    break
                _total_length -= 1
            except Exception:
                _total_length -= 1


    def handle_recv_data(self, recv_data, statuses, messages):
        try:
            _trying_unpacked, _left_buffer = unpack(recv_data)
            _msgidx = _trying_unpacked.msgid - BIAS_MSGID
            _is_deleted = _trying_unpacked.code > 0
            _is_right = False
            _right_status = statuses[_msgidx]
            if _is_deleted:
                if _right_status > 0:
                    _is_right = True
            else:
                if _right_status == 0:
                    _is_right = True
            
            if _is_right:
                self.length_right += 1
            else:
                logging.warning('Wrong Predict :: txt = [{}]   ans = [{}]'.format(messages[_msgidx], statuses[_msgidx]))

            statuses[_msgidx] = -1
            return _left_buffer

        except Exception as exp:
            logging.error(exp)
            print('_msgidx: ', _msgidx)
            print('_trying_unpacked: ', _trying_unpacked.msgid, _trying_unpacked.code)
            raise Exception(exp)


    def handle(self, *args, **options):
        _handle_start_time = time.time()
        file_path = options.get('input_excel_path', None)
        port = options.get('port')
        host = options.get('host')
        is_multiple = options.get('multiple', False)
        time_gap = options.get('time_gap', None)

        if port is None:
            port = 8025
        else:
            port = int(port)
            
        if host is None:
            host = '127.0.0.1'

        if time_gap is None:
            time_gap = 0.3
        else:
            time_gap = float(time_gap)

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
        while_recv_thread = threading.Thread(target= self.while_recv_data, args = (statuses, messages))
        while_recv_thread.start()

        cmd_ints = [0x000001, 0x040001, 0x040002, 0x040003, 0x040004, 0x041003]

        num = 5
        command_hex = cmd_ints[num]

        keep_doing = True
        msgid = 0
        length_messages = len(messages)

        length_right = 0
        while keep_doing and msgid < length_messages:

            try:
                msgtxt = messages[msgid]

                if msgtxt:
                    # print('sending txt: ', msgtxt)
                    # packed = pack(command_hex, msgid=msgid+BIAS_MSGID, msgtxt=msgtxt)
                    packed = pack(command_hex, msgid=msgid+BIAS_MSGID, json={'msg': msgtxt, 'roomid': 'localhost'})

                    if msgid % 10 == 0:
                        print(' {:2.1%}'.format(msgid / length_messages), end="\r")
                else:
                    print('msgtxt wrong: ', msgtxt)
                    continue
                
                self.client.send(packed)
                
                if msgid % 4 == 0:
                    time.sleep(time_gap)
                else:
                    if is_multiple:
                        time.sleep(0.001)
                    else:
                        time.sleep(0.1)
                
                msgid += 1

            except KeyboardInterrupt:

                keep_doing = False

        
        if keep_doing:
            while_recv_thread.join()

        length_right = self.length_right
        length_timeout = self.length_timeout_no_recv

        for i in range(len(statuses)):
            if statuses[i] >= 0:
                print('None Response Message: ', messages[i])
        print('disconnect from tcp server.')
        print('Length Of Message: ', length_messages, 'Count Of Threading: ', threading.active_count())
        print('Sum Of Spending Receive Second: ', self.spend_recv_second, ' Executed Time: ', time.time() - _handle_start_time)
        print('right ratio : {:2.2%}  ,  length of timeout : {}'.format(length_right / length_messages, length_timeout))
        client.close()

