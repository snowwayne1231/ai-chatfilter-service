import socket
import os, sys, getopt
from chat_package import pack, unpack
from configparser import RawConfigParser
from dataparser.apps import ExcelParser

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
DIR = os.path.dirname(os.path.abspath(__file__))

config_key = RawConfigParser()
config_key.read(DIR+'/keys.cfg')

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
# host = '172.16.20.120'
port = 8025
bufsize = 1024
file_path = None
messages = []

argvs = sys.argv[1:]

try:
    opts, args = getopt.getopt(argvs, "h:p:b:i:")
except getopt.GetoptError as err:
    print(err)
    sys.exit(2)

for o, a in opts:
    if o == "-p":
        port = int(a)

    if o == "-h":
        host = str(a)

    if o == '-b':
        bufsize = int(a)

    if o == '-i':
        file_path = os.getcwd() + '/' + str(a)


if file_path:

    ep = ExcelParser(file=file_path)
    basic_model_columns = [['VID', '房號'], ['LOGINNAME', '會員號'], ['MESSAGE', '聊天信息']]
    row_list = ep.get_row_list(column=basic_model_columns)
    for r in row_list:
        _loc = r[2]
        if _loc:
            messages.append(_loc)

else:

    messages = [1,2,3,4]

addr = (host, port)

client.connect(addr)

cmd_options = ['hearting', 'login', 'login response', 'chatting', 'chat response']
cmd_ints = [0x000001, 0x040001, 0x040002, 0x040003, 0x040004]

num = 3
keep_doing = True
msgid = 0
length_messages = len(messages)

while keep_doing and msgid < length_messages:

    try:
        msgtxt = messages[msgid]
        command_hex = cmd_ints[num]

        

        if msgtxt:
            packed = pack(command_hex, msgid=msgid, msgtxt=msgtxt)
        else:
            break
        
        client.send(packed)

        recv_data = client.recv(bufsize)
        if not recv_data:
            break

        print('===== receive data =====')
        # print (recv_data.decode('utf-8'))
        trying_unpacked = unpack(recv_data)
        
        print(trying_unpacked)
        print('=========================')

        msgid += 1

    except KeyboardInterrupt:

        keep_doing = False


print('disconnect from tcp server.')
client.close()
