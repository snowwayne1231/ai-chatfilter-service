import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# host = '127.0.0.1'
host = '172.16.20.120'
port = 8025
bufsize = 4096
addr = (host, port)

client.connect(addr)

while True:
    data = input()
    if not data or data=='exit':
        break

    client.send(data.encode('utf-8'))

    recv_data = client.recv(bufsize)
    if not recv_data:
        break

    print('===== receive data ====')
    print (recv_data.decode('utf-8'))

client.close()
