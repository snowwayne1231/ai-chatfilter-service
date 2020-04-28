from socketserver import StreamRequestHandler as Tcp
import socketserver
import os, sys, getopt, datetime, json
from chat_package import pack, unpack
from configparser import RawConfigParser
from to_websocket import WebsocketThread
import logging
sys.path.append("..")
# from service import instance


SOCKET_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SOCKET_DIR)

config_setting = RawConfigParser()
config_setting.read(BASE_DIR+'/setting.ini')
config_version = RawConfigParser()
config_version.read(BASE_DIR+'/version.cfg')
config_keys = RawConfigParser()
config_keys.read(SOCKET_DIR+'/keys.cfg')

logging_level = logging.DEBUG if bool('True' in config_setting.get('MAIN', 'DEBUG')) else logging.INFO
logging.basicConfig(format='[%(levelname)s]%(asctime)s %(message)s', datefmt='(%m/%d) %I:%M:%S %p :: ', level=logging_level)

host = '0.0.0.0'
port = 8025
web_socket_port = 8000
version = '{}.{}'.format(config_version.get('MAIN', 'V'), config_version.get('MAIN', 'SUR'))
serverid = config_keys.get('SERVER', 'ID')
sig = config_keys.get('SERVER', 'PWD')

websocket_thread = None

g_max_msg_legnth = 255

# main_service = instance.get_main_service()

def log_except_hook(*exc_info):
    print('log_except_hook')
    print(exc_info)
    


class socketTcp(Tcp):
    def handle(self):
        logging.info('**TCPSocket Version[{}] clinet has connected, address: {}'.format(version, self.client_address))
        while True:
            recived = self.request.recv(1024)
            if not recived:
                break
            
            unpacked_data = unpack(recived)

            packed_res = pack(0x000001)

            now = datetime.datetime.now()

            if unpacked_data.cmd == 0x000001:
                pass

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

            elif unpacked_data.cmd == 0x040003:
                logging.debug('Recived Package is [ Chat ]')
                # logging.debug('msgid: {}'.format(unpacked_data.msgid))
                # logging.debug('msgtxt: {}'.format(unpacked_data.msgtxt))
                # logging.debug('msgbuffer: {}'.format(unpacked_data.msgbuffer))
                # logging.debug('msgsize: {}'.format(unpacked_data.msgsize))

                status_code = 0

                if websocket_thread and websocket_thread.is_active:
                    
                    _msg = unpacked_data.msgtxt if len(unpacked_data.msgtxt) < g_max_msg_legnth else unpacked_data.msgtxt[:g_max_msg_legnth]
                    if isinstance(unpacked_data.msgid, int) and _msg:
                        ai_results = websocket_thread.thinking(msg=_msg, msgid=unpacked_data.msgid)
                        prediction = ai_results.get('prediction', None)
                    else:
                        prediction = None
                    
                    if prediction:
                        if prediction != 0:
                            status_code = 5
                            logging.info('Message be blocked = id: {} txt: {}'.format(unpacked_data.msgid, unpacked_data.msgtxt))
                    
                else:

                    logging.error('Websocket is Not Working. [txt: {}]'.format(unpacked_data.msgtxt))

                packed_res = pack(0x040004, msgid=unpacked_data.msgid, code=status_code)

            elif unpacked_data.cmd == 0x041003:
                logging.debug('Recived Package is [ Chat Json ]')
                # logging.debug('json string: {}'.format(unpacked_data.jsonstr))

                status_code = 0

                if websocket_thread and websocket_thread.is_active:

                    _msg = unpacked_data.msg if len(unpacked_data.msg) < g_max_msg_legnth else unpacked_data.msg[:g_max_msg_legnth]

                    if isinstance(unpacked_data.msgid, int) and _msg:

                        ai_results = websocket_thread.thinking(msg=_msg, msgid=unpacked_data.msgid, room=unpacked_data.roomid)
                        prediction = ai_results.get('prediction', None)
                    
                    if prediction and prediction != 0:
                        status_code = 5
                        logging.info('Message be blocked = id: {} msg: {}'.format(unpacked_data.msgid, _msg))
                    
                else:

                    logging.error('Websocket is Not Working [JSON: {}].'.format(unpacked_data.jsonstr))

                packed_res = pack(0x040004, msgid=unpacked_data.msgid, code=status_code)

            elif unpacked_data.cmd == 0x040004:
                logging.debug('Recived Package is [ Chat Response ]')
                logging.debug('msgid: {}'.format(unpacked_data.msgid))
                logging.debug('code: {}'.format(unpacked_data.code))

            else:
                pass
                logging.debug('Recived Package Unknow.')
            
            self.request.sendall(packed_res)
            # self.request.sendall(recived)
        
        logging.info('**TCPSocket clinet disconnected, address: {}'.format(self.client_address))

    def handle_error(self):
        logging.error('TCPSocket Handle Error!!')

    def server_close(self):
        logging.error('TCPSocket Server Closed!!!')



if __name__ == '__main__':

    argvs = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argvs, "hp:w:")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    for o, a in opts:
        if o == "-p":
            port = int(a)
        if o == '-w':
            web_socket_port = int(a)

    
    addr = (host, port)
    # server = socketserver.TCPServer(addr, socketTcp)
    server = socketserver.ThreadingTCPServer(addr, socketTcp)
    
    logging.info('TCP Socket Server launched on port :: {}'.format(port))

    websocket_thread = WebsocketThread("Websocket Thread-1", web_socket_port)
    
    try:

        websocket_thread.start()
        
        server.serve_forever()

    except KeyboardInterrupt:

        # websocket_thread.join()
        # print('Keypress-Stop')
        websocket_thread.stop()
        
        logging.info('TCP Socket Server Stoped.')

    except Exception as err:
        
        websocket_thread.stop()

        logging.error(err)

    server.shutdown()

    sys.exit(2)
    

    
    