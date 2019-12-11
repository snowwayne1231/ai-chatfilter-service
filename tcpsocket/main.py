from socketserver import StreamRequestHandler as Tcp
import socketserver
import os, sys, getopt, datetime
from chat_package import pack, unpack
from configparser import RawConfigParser

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
SOCKET_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SOCKET_DIR)

config_version = RawConfigParser()
config_version.read(BASE_DIR+'/version.cfg')
config_keys = RawConfigParser()
config_keys.read(SOCKET_DIR+'/keys.cfg')

host = '0.0.0.0'
port = 8025
version = '{}.{}'.format(config_version.get('MAIN', 'V'), config_version.get('MAIN', 'SUR'))
serverid = config_keys.get('SERVER', 'ID')
sig = config_keys.get('SERVER', 'PWD')

class socketTcp(Tcp):
    def handle(self):
        print('**TCPSocket Version[{}] clinet has connected, address: '.format(version), self.client_address, flush=True)
        while True:
            recived = self.request.recv(1024)
            if not recived:
                break
            
            unpacked_data = unpack(recived)

            packed_res = pack(0x000001)

            now = datetime.datetime.now()
            print('====<Recived cmd/size>: ', unpacked_data.cmd, '/', unpacked_data.size, ' | ', now, flush=True)

            if unpacked_data.cmd == 0x000001:
                print('Package is [ Hearting ]', flush=True)
                

            elif unpacked_data.cmd == 0x040001:
                print('Package is [ Login ]', flush=True)
                
                is_matched = serverid == unpacked_data.serverid and sig == unpacked_data.sig

                if is_matched:
                    print('Login Successful serverid: ', serverid, flush=True)
                    server_code = 0
                else:
                    print('Login Failed. unpacked_data.sig: ', unpacked_data.sig , flush=True)
                    server_code = 1

                packed_res = pack(0x040002, code=server_code)

            elif unpacked_data.cmd == 0x040002:
                print('Package is [ Login Response ]', flush=True)
                print('code: ', unpacked_data.code, flush=True)

            elif unpacked_data.cmd == 0x040003:
                print('Package is [ Chat ]', flush=True)
                print('msgid: ', unpacked_data.msgid, flush=True)
                print('msgtxt: ', unpacked_data.msgtxt, flush=True)
                print('msgsize: ', unpacked_data.msgsize, flush=True)

                packed_res = pack(0x040004, msgid=unpacked_data.msgid, code=0)

            elif unpacked_data.cmd == 0x040004:
                print('Package is [ Chat Response ]', flush=True)
                print('msgid: ', unpacked_data.msgid, flush=True)
                print('code: ', unpacked_data.code, flush=True)

            else:
                pass
                print('Package Unknow.', flush=True)
            
            self.request.sendall(packed_res)
            # self.request.sendall(recived)


if __name__ == '__main__':

    argvs = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argvs, "hp:")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    for o, a in opts:
        if o == "-p":
            port = int(a)


    addr = (host, port)
    # server = socketserver.TCPServer(addr, socketTcp)
    server = socketserver.ThreadingTCPServer(addr, socketTcp)
    print('TCP Socket Server launched on port :: ', port)
    server.serve_forever()
    