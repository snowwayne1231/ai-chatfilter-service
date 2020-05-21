from tcpsocket.to_websocket import WebsocketThread
from tcpsocket.tcp import socketTcp

import socketserver, socket
import os, sys, getopt
import logging, time
# sys.path.append("..")
from service import instance



class LaunchTcpSocket():

    addr = (None, None)
    server = None
    service_instance = None
    websocket = None
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
        self.ws_url = self.websocket.get_ws_url()

        self.start()

    
    def handler_factory(self):
        callback = self.handle_tcp_callback
        on_open = self.handle_tcp_open
        on_close = self.handle_tcp_close
        service_instance = self.service_instance
        
        def createHandler(*args, **keys):
            return socketTcp(callback, service_instance, on_open, on_close, *args, **keys)
        return createHandler
    

    def handle_tcp_callback(self, data, prediction, status_code):
        if prediction is None:
            return
        
        if self.websocket and self.websocket.is_active:

            if data.cmd == 0x040003 or data.cmd == 0x041003:
                _msgid = data.msgid
                _msg = data.msg
                _room = data.roomid if hasattr(data, 'roomid') else ''
                self.websocket.send_msg(msgid=_msgid, msg=_msg, room=_room, prediction=prediction)
        else:
            logging.error('Websocket is Not Working. [txt: {}]'.format(data.msg))

    
    def handle_tcp_open(self):
        self.is_tcp_connecting = True


    def handle_tcp_close(self):
        self.is_tcp_connecting = False


    def on_websocket_message(self, msgid, message):
        print('on_websocket_message msgid: ', msgid)
        if msgid == self.websocket.key_send_train_remotely:
            print('message lenth: ', len(message))
            print('self.server: ', self.server)
            print('service_instance: ', self.service_instance)
            self.service_instance.fit_pinyin_model()

    

    def start(self):
        try:

            self.websocket.start()

            while not self.websocket.is_active:
                logging.debug('Watting For Connecting.. (Tcpsocket to Websocket).')
                time.sleep(0.5)

            self.pinyin_data = self.websocket.get_remote_pinyin_data()
            self.service_instance = instance.get_main_service()
            self.service_instance.open_mind(pinyin_data=self.pinyin_data)

            self.server = socketserver.ThreadingTCPServer(self.addr, self.handler_factory())
            logging.info('TCP Socket Server launched on port :: {}'.format(self.addr[1]))
            self.server.serve_forever()

        except KeyboardInterrupt:

            self.websocket.stop()

            logging.info('TCP Socket Server Stoped.')

        except Exception as err:
            
            self.websocket.stop()

            logging.error(err)

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
    

    
    
    
    

    
    