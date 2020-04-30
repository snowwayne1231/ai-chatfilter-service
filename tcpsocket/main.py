from tcpsocket.to_websocket import WebsocketThread
from tcpsocket.tcp import socketTcp

import socketserver
import os, sys, getopt
import logging
# sys.path.append("..")
# from service import instance



class LaunchTcpSocket():

    addr = (None, None)
    server = None
    websocket = None

    def __init__(self, host, port, webhost, webport):
        # print('LaunchTcpSocket: ', host, port)
        self.addr = (host, port)
        self.server = socketserver.ThreadingTCPServer(self.addr, self.handler_factory())
        self.websocket = WebsocketThread("Websocket Thread-1", host=webhost, port=webport)

        logging.info('TCP Socket Server launched on port :: {}'.format(self.addr[1]))
        self.start()

    
    def handler_factory(self):
        callback = self.handle_callback
        def createHandler(*args, **keys):
            return socketTcp(callback, *args, **keys)
        return createHandler
    

    def handle_callback(self, data, prediction, status_code):
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
    

    def start(self):
        try:

            self.websocket.start()
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
    

    
    
    
    

    
    