
from configparser import RawConfigParser
from dataparser.apps import ExcelParser
from socketserver import StreamRequestHandler as Tcp
from tcpsocket.chat_package import pack, unpack
# from queue import Queue
import logging
import os, datetime, json, threading

SOCKET_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SOCKET_DIR)

config_setting = RawConfigParser()
config_setting.read(BASE_DIR+'/setting.ini')
config_keys = RawConfigParser()
config_keys.read(SOCKET_DIR+'/keys.cfg')
config_version = RawConfigParser()
config_version.read(BASE_DIR+'/version.cfg')

version = '{}.{}'.format(config_version.get('MAIN', 'V'), config_version.get('MAIN', 'SUR'))
serverid = config_keys.get('SERVER', 'ID')
sig = config_keys.get('SERVER', 'PWD')

logging_level = logging.DEBUG if bool('True' in config_setting.get('MAIN', 'DEBUG')) else logging.INFO
logging.basicConfig(format='[%(levelname)s]%(asctime)s %(message)s', datefmt='(%m/%d) %I:%M:%S %p :: ', level=logging_level)

threadLock = threading.Lock()

class LockThread(threading.Thread):
    def __init__(self, target, args):
        threading.Thread.__init__(self)
        self.target = target
        self.args = args

    def run(self):
        try:
            if threadLock.acquire(timeout=3):
                self.target(*self.args)
            
        except Exception as exp:

            logging.error('LockThread Something Wrong.')
            print(exp)

        finally:
            threadLock.release()
            del self.target, self.args
            


class socketTcp(Tcp):

    callback = None
    on_client_open = None
    on_client_close = None
    service_instance = None
    nickname_filter_instance = None
    # thread_queue = Queue(4)
    

    def __init__(self, callback, service_instance, on_client_open = None, on_client_close = None, nickname_filter_instance = None, *args, **keys):
        self.callback = callback
        self.on_client_open = on_client_open
        self.on_client_close = on_client_close
        self.service_instance = service_instance
        self.nickname_filter_instance = nickname_filter_instance
        
        super().__init__(*args, **keys)


    def handle_recive_threading(self, recived):
        unpacked_data = unpack(recived)

        status_code = -1
        prediction = None

        if unpacked_data.cmd == 0x000001:
            logging.debug('Recived Package is [ Check Hearting ]')
            packed_res = pack(0x000001) # hearting

        elif unpacked_data.cmd == 0x040001:
            logging.debug('Recived Package is [ Login ]')
            
            is_matched = serverid == unpacked_data.serverid and sig == unpacked_data.sig

            if is_matched:
                logging.debug('Login Successful serverid: {}'.format(serverid))
                server_code = 0
            else:
                logging.debug('Login Failed. unpacked.sig: {}'.format(unpacked_data.sig))
                server_code = 1

            packed_res = pack(0x040002, code=server_code)

        elif unpacked_data.cmd == 0x040002:
            logging.debug('Recived Package is [ Login Response ]')
            packed_res = pack(0x000001)

        elif unpacked_data.cmd == 0x040003:
            logging.debug('Recived Package is [ Chat ] msg: {}'.format(unpacked_data.msg))
            # logging.debug('msgid: {}'.format(unpacked_data.msgid))
            # logging.debug('msgtxt: {}'.format(unpacked_data.msg))
            # logging.debug('msgbuffer: {}'.format(unpacked_data.msgbuffer))
            # logging.debug('msgsize: {}'.format(unpacked_data.msgsize))

            status_code = 0
            _msg = unpacked_data.msg
            if isinstance(unpacked_data.msgid, int) and _msg:
                ai_results = self.service_instance.think(message=_msg)
                prediction = ai_results.get('prediction', None)
            
            if prediction:
                if prediction > 0:
                    status_code = 5
                    logging.info('Message be blocked = id: {} txt: {}'.format(unpacked_data.msgid, unpacked_data.msg))

            packed_res = pack(0x040004, msgid=unpacked_data.msgid, code=status_code)

        elif unpacked_data.cmd == 0x041003:
            logging.debug('Recived Package is [ Chat Json ] msg: {} | room: {}'.format(unpacked_data.msg, unpacked_data.roomid))
            # logging.debug('json string: {}'.format(unpacked_data.jsonstr))

            status_code = 0
            _msg = unpacked_data.msg

            if isinstance(unpacked_data.msgid, int) and _msg:

                ai_results = self.service_instance.think(message=_msg, room=unpacked_data.roomid)
                prediction = ai_results.get('prediction', None)
            

            if prediction and prediction > 0:
                status_code = 5
                logging.info('Message be blocked = id: {} msg: {}'.format(unpacked_data.msgid, _msg))
            

            packed_res = pack(0x040004, msgid=unpacked_data.msgid, code=status_code)

        elif unpacked_data.cmd == 0x040004:
            logging.debug('Recived Package is [ Chat Response ]')
            logging.debug('msgid: {}'.format(unpacked_data.msgid))
            logging.debug('code: {}'.format(unpacked_data.code))
            packed_res = pack(0x000001)

        elif unpacked_data.cmd == 0x040007:
            logging.debug('Recived Package is [ Nickname Change Request ] id: {} | name: {} | size: {}'.format(unpacked_data.reqid, unpacked_data.nickname, unpacked_data.size))

            if self.nickname_filter_instance:

                ai_results = self.nickname_filter_instance.think(nickname=unpacked_data.nickname)
                code = ai_results.get('code', 0)

                if code and code > 0:
                    logging.info('Nickname Change Request be blocked = reqid: {} | code: {}'.format(unpacked_data.reqid, code))

            else:

                code = 0

            packed_res = pack(0x040008, reqid=unpacked_data.reqid, code=code)
            prediction = code

        else:
            
            logging.error('Recived Package Unknow.')
            packed_res = pack(0x000001)
        
        try:
            self.request.sendall(packed_res)
            if self.callback and prediction is not None:
                self.callback(unpacked_data, int(prediction), status_code)
        except Exception as exp:
            logging.error('Request Sendall Failed.')
            print(exp)
    


    def handle(self):
        logging.info('**TCPSocket Version[{}] clinet has connected, address: {}'.format(version, self.client_address))
        self.on_client_open()
        while True:
            recived = self.request.recv(1024)
            if not recived:
                logging.error('Not Recived [ {} ]'.format(recived))
                break

            # now = datetime.datetime.now()
            
            _thread = LockThread(target = self.handle_recive_threading, args = (recived,))
            _thread.start()
            

            # self.request.sendall(recived)
        
        logging.info('**TCPSocket clinet disconnected, address: {}'.format(self.client_address))
        for thread in threading.enumerate(): 
            print(thread.join())
        
        self.on_client_close()
    

    def handle_error(self):
        logging.error('TCPSocket Handle Error!!')
        self.on_client_close()

    def server_close(self):
        logging.error('TCPSocket Server Closed!!!')
        self.on_client_close()

