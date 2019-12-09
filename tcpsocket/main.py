from socketserver import StreamRequestHandler as Tcp
import socketserver
import sys, getopt
from chat_package import pack, unpack

host = '0.0.0.0'
port = 8025
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

class socketTcp(Tcp):
    def handle(self):
        print('Clinet has connected, address: ', self.client_address, flush=True)
        while True:
            recived = self.request.recv(1024)
            if not recived:
                break
            
            unpacked_data = unpack(recived)
            
            print('====<Recived cmd/size>: ', unpacked_data.cmd, '/', unpacked_data.size, flush=True)

            if unpacked_data.cmd == 0x000001:
                print('==Hearting', flush=True)
            elif unpacked_data.cmd == 0x040001:
                print('==Login', flush=True)
                print('serverid: ', unpacked_data.serverid, flush=True)
            elif unpacked_data.cmd == 0x040002:
                print('==Login res', flush=True)
                print('code: ', unpacked_data.code, flush=True)
            elif unpacked_data.cmd == 0x040003:
                print('==Chatting', flush=True)
                print('msgid: ', unpacked_data.msgid, flush=True)
                print('msgtxt: ', unpacked_data.msgtxt, flush=True)
                print('msgsize: ', unpacked_data.msgsize, flush=True)
            elif unpacked_data.cmd == 0x040004:
                print('==Chatting res', flush=True)
                print('msgid: ', unpacked_data.msgid, flush=True)
                print('code: ', unpacked_data.code, flush=True)
            else:
                pass
                print('==Unknow: ', flush=True)
            

            self.request.sendall(recived)


if __name__ == '__main__':


    # server = socketserver.TCPServer(addr, socketTcp)
    server = socketserver.ThreadingTCPServer(addr, socketTcp)
    print('Server launched on port :: ', port)
    server.serve_forever()
    