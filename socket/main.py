from socketserver import StreamRequestHandler as Tcp
import socketserver

host = '0.0.0.0'
port = 8025
addr = (host, port)

class socketTcp(Tcp):
    def handle(self):
        print('clinet has connected, address: ', self.client_address)
        while True:
            recived = self.request.recv(4096)
            if not recived:
                break

            unicode_string = recived.decode('utf-8')
            print('unicode string recived: ', unicode_string)
            self.request.sendall(recived)

if __name__ == '__main__':


    # server = socketserver.TCPServer(addr, socketTcp)
    server = socketserver.ThreadingTCPServer(addr, socketTcp)
    print('server launched.')
    server.serve_forever()
    