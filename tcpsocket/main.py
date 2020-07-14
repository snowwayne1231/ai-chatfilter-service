from tcpsocket.to_websocket import WebsocketThread
from tcpsocket.tcp import socketTcp

from http.client import HTTPConnection
import socketserver, socket
import os, sys, getopt
import logging, time
# sys.path.append("..")
from service import instance
from ai.helper import get_pinyin_path, get_grammar_path, get_pinyin_dictionary_path
from dataparser.classes.store import ListPickle



class LaunchTcpSocket():

    addr = (None, None)
    server = None
    service_instance = None
    nickname_filter_instance = None
    websocket = None
    websocket_host = None
    websocket_port = None
    ws_url = ''
    remote_vocabulary = []
    local_host = (None, None)
    is_tcp_connecting = False

    def __init__(self, host, port, webhost, webport):
        # print('LaunchTcpSocket: ', host, port)
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name)
        self.local_host = (host_name, host_ip)

        self.addr = (host, port)
        self.websocket = WebsocketThread("Websocket Thread-1", host=webhost, port=webport, local_host=self.local_host, on_message_callback=self.on_websocket_message)
        self.websocket_host = webhost
        self.websocket_port = webport
        self.ws_url = self.websocket.get_ws_url()

        self.start()

    
    def handler_factory(self):
        callback = self.handle_tcp_callback
        on_open = self.handle_tcp_open
        on_close = self.handle_tcp_close
        service_instance = self.service_instance
        nickname_filter_instance = self.nickname_filter_instance
        
        def createHandler(*args, **keys):
            return socketTcp(callback, service_instance, on_open, on_close, nickname_filter_instance, *args, **keys)
        return createHandler
    

    def handle_tcp_callback(self, data, prediction, status_code = 0):
        if prediction is None:
            return
        
        if self.websocket and self.websocket.is_active:

            if data.cmd == 0x040003 or data.cmd == 0x041003:
                #
                _msgid = data.msgid
                _msg = data.msg
                _room = data.roomid if hasattr(data, 'roomid') else ''
                self.websocket.send_msg(msgid=_msgid, msg=_msg, room=_room, prediction=prediction)
            elif data.cmd == 0x040007:
                # nickname change
                _nickname = data.nickname
                logging.debug('[handle_tcp_callback][Send To Websocket Nickname] prediction: {} | type: {}'.format(prediction, type(prediction)))
                logging.debug('_nickname: {} | type: {}'.format(_nickname, type(_nickname)))
                self.websocket.send_msg(msgid=self.websocket.key_change_nickname_request, msg=_nickname, prediction=prediction)
                
        else:
            logging.error('Websocket is Not Working. [txt: {}]'.format(data.msg))

    
    def handle_tcp_open(self):
        self.is_tcp_connecting = True


    def handle_tcp_close(self):
        self.is_tcp_connecting = False


    def on_websocket_message(self, msgid, message):
        print('on_websocket_message msgid: ', msgid)
        

    

    def start(self):
        try:

            self.websocket.start()
            _max_times = 50
            while not self.websocket.is_active:
                logging.debug('Watting For Connecting.. (Tcpsocket to Websocket).')
                time.sleep(0.5)
                _max_times -= 1
                if _max_times <= 0:
                    break


            if self.websocket_host != '127.0.0.1' and self.websocket.is_active:

                _http_cnn = HTTPConnection(self.websocket_host, self.websocket_port)

                _http_cnn.request('GET', '/api/model/pinyin')
                _http_res = _http_cnn.getresponse()
                if _http_res.status == 200:
                    with open(get_pinyin_path()+'/model.h5', 'wb+') as f:
                        while True:
                            _buf = _http_res.read()
                            if _buf:
                                f.write(_buf)
                            else:
                                break
                    logging.info('Download Remote Pinyin Model Done.')
                else:
                    logging.error('Download Remote Pinyin Model Failed.')

                _http_cnn.request('GET', '/api/model/grammar')
                _http_res = _http_cnn.getresponse()
                if _http_res.status == 200:
                    with open(get_grammar_path()+'/model.h5', 'wb+') as f:
                        while True:
                            _buf = _http_res.read()
                            if _buf:
                                f.write(_buf)
                            else:
                                break
                    logging.info('Download Remote Grammar Model Done.')
                else:
                    logging.error('Download Remote Grammar Model Failed.')
            

            _pinyin_data_pk = ListPickle(get_pinyin_dictionary_path() + '/data')
            
            if self.websocket.is_active:
                self.pinyin_data = self.websocket.get_remote_pinyin_data()
                _pinyin_data_pk.save([self.pinyin_data])
            else:
                self.pinyin_data = _pinyin_data_pk.get_list()[0]

            self.service_instance = instance.get_main_service()
            self.service_instance.open_mind(pinyin_data=self.pinyin_data)

            self.nickname_filter_instance = instance.get_nickname_filter()

            self.server = socketserver.ThreadingTCPServer(self.addr, self.handler_factory())
            logging.info('TCP Socket Server launched on port :: {}'.format(self.addr[1]))
            self.server.serve_forever()

        except KeyboardInterrupt:

            self.websocket.stop()

            logging.info('TCP Socket Server Stoped.')

        except Exception as err:
            
            self.websocket.stop()

            logging.error(err)

        if self.server:
            self.server.shutdown()
        sys.exit(2)



host = '0.0.0.0'
port = 8025
web_socket_host = '127.0.0.1'
web_socket_port = 8000

# main_service = instance.get_main_service()


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

    
    main = LaunchTcpSocket(host, port, web_socket_host, web_socket_port)

    # server = socketserver.TCPServer(addr, socketTcp)
    

    
    
    
    

    
    