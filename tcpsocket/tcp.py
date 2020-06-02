
from configparser import RawConfigParser
from socketserver import StreamRequestHandler as Tcp
from tcpsocket.chat_package import pack, unpack
import logging
import os, datetime, json

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


class socketTcp(Tcp):

    callback = None
    on_client_open = None
    on_client_close = None
    service_instance = None
    nickname_filter_instance = None
    

    def __init__(self, callback, service_instance, on_client_open = None, on_client_close = None, nickname_filter_instance = None, *args, **keys):
        self.callback = callback
        self.on_client_open = on_client_open
        self.on_client_close = on_client_close
        self.service_instance = service_instance
        self.nickname_filter_instance = nickname_filter_instance
        
        super().__init__(*args, **keys)
    

    def handle(self):
        logging.info('**TCPSocket Version[{}] clinet has connected, address: {}'.format(version, self.client_address))
        self.on_client_open()
        while True:
            recived = self.request.recv(1024)
            if not recived:
                break
            
            unpacked_data = unpack(recived)

            # packed_res = pack(0x000001)

            now = datetime.datetime.now()

            status_code = -1
            prediction = None

            if unpacked_data.cmd == 0x000001:
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
                logging.debug('Recived Package is [ Chat Json ] msg: {}'.format(unpacked_data.msg))
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
                logging.debug('Recived Package is [ Nickname Change Request ] id: {} | name: {}'.format(unpacked_data.reqid, unpacked_data.nickname))

                if self.nickname_filter_instance:

                    ai_results = self.nickname_filter_instance.think(nickname=unpacked_data.nickname)
                    code = ai_results.get('code', 0)

                else:

                    code = 0

                packed_res = pack(0x040008, reqid=unpacked_data.reqid, code=code)

            else:
                logging.debug('Recived Package Unknow.')
                packed_res = pack(0x000001)
            
            
            self.request.sendall(packed_res)
            if self.callback and prediction is not None:
                self.callback(unpacked_data, int(prediction), status_code)
            # self.request.sendall(recived)
        
        logging.info('**TCPSocket clinet disconnected, address: {}'.format(self.client_address))
        self.on_client_close()

    def handle_error(self):
        logging.error('TCPSocket Handle Error!!')
        self.on_client_close()

    def server_close(self):
        logging.error('TCPSocket Server Closed!!!')
        self.on_client_close()

