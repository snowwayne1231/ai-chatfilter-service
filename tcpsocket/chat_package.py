import struct
import json
import logging


def pack(cmd, **options):
    
    size = 0
    package = None

    if cmd == HeartingPackage.m_cmd:

        size = struct.calcsize(HeartingPackage.fmt)
        package = struct.pack(HeartingPackage.fmt, cmd, size)

    elif cmd == LoginPackage.m_cmd:

        serverid = options.get('serverid', '')
        sig = options.get('sig', '')

        size = struct.calcsize(LoginPackage.fmt)
        package = struct.pack(LoginPackage.fmt, cmd, size, serverid.encode('utf-8'), sig.encode('utf-8'))

    elif cmd == LoginResponsePackage.m_cmd:

        code = options.get('code', 0x000000)

        size = struct.calcsize(LoginResponsePackage.fmt)
        package = struct.pack(LoginResponsePackage.fmt, cmd, size, code)

    elif cmd == ChatFilterPackage.m_cmd:

        msgid = options.get('msgid', 0x000000)
        msgtxt = options.get('msgtxt', '')
        msg_bytes = bytes(msgtxt, 'utf-8')

        msgsize = len(msg_bytes)
        
        size = struct.calcsize(ChatFilterPackage.fmt) + msgsize

        package = struct.pack(ChatFilterPackage.fmt, cmd, size, msgid, msgsize) + msg_bytes
        # package = struct.pack('!4i100s', cmd, size, msgid, msgsize, msgtxt.encode('utf-8'))

    elif cmd == ChatWithJSONPackage.m_cmd:

        json_data = options.get('json', {})
        msgid = options.get('msgid', 0x000000)
        msgtxt = json_data.get('msg', '')
        roomid = json_data.get('roomid', 'none')

        json_byte = bytes(json.dumps({'msg': msgtxt, 'roomid': roomid}), 'utf-8')
        jsonsize = len(json_byte)

        size = struct.calcsize(ChatWithJSONPackage.fmt) + jsonsize
        package = struct.pack(ChatWithJSONPackage.fmt, cmd, size, msgid, jsonsize) + json_byte

    elif cmd == ChatFilterResponsePackage.m_cmd:

        msgid = options.get('msgid', 0x000000)
        code = options.get('code', 0x000000)

        size = struct.calcsize(ChatFilterResponsePackage.fmt)
        package = struct.pack(ChatFilterResponsePackage.fmt, cmd, size, msgid, code)

    elif cmd == NickNameFilterRequestPackage.m_cmd:

        reqid = options.get('reqid', 0x000000)
        nickname = options.get('nickname', '')
        byte_nickname = bytes(nickname, 'utf-8')

        size = struct.calcsize(NickNameFilterRequestPackage.fmt) + len(byte_nickname)

        package = struct.pack(NickNameFilterRequestPackage.fmt, cmd, size, reqid) + byte_nickname

    elif cmd == NickNameFilterResponsePackage.m_cmd:

        reqid = options.get('reqid', 0x000000)
        code = options.get('code', 0x000000)

        size = struct.calcsize(NickNameFilterResponsePackage.fmt)
        package = struct.pack(NickNameFilterResponsePackage.fmt, cmd, size, reqid, code)
    

    return package


def unpack(buffer):
    (cmd,) = struct.unpack('!i', buffer[:4])

    # print(' -- unpack cmd: ', cmd)

    if cmd == HeartingPackage.m_cmd:

        return HeartingPackage(buffer)

    elif cmd == LoginPackage.m_cmd:

        return LoginPackage(buffer)

    elif cmd == LoginResponsePackage.m_cmd:

        return LoginResponsePackage(buffer)

    elif cmd == ChatFilterPackage.m_cmd:

        return ChatFilterPackage(buffer)

    elif cmd == ChatWithJSONPackage.m_cmd:

        return ChatWithJSONPackage(buffer)

    elif cmd == ChatFilterResponsePackage.m_cmd:

        return ChatFilterResponsePackage(buffer)

    elif cmd == NickNameFilterRequestPackage.m_cmd:

        return NickNameFilterRequestPackage(buffer)

    elif cmd == NickNameFilterResponsePackage.m_cmd:

        return NickNameFilterResponsePackage(buffer)
    

    return BasicStructPackage(buffer)


class BasicStructPackage():
    m_cmd = 0x000000
    cmd = 0x000000
    size = 0x000000
    fmt = '!2i'

    def __init__(self, buffer):
        self.parse(buffer)

    def parse(self, buffer):
        print('BasicStructPackage buffer: ', buffer)
        cmd, size = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        


class HeartingPackage(BasicStructPackage):
    m_cmd = 0x000001
    timestamp = 0

    def parse(self, buffer):
        cmd, size = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
    

class LoginPackage(BasicStructPackage):
    m_cmd = 0x040001
    fmt = '!2i16s16s'
    serverid = ''   # chat server id 
    sig = ''    # login password

    def parse(self, buffer):
        cmd, size, serverid, sig = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        self.serverid = serverid.decode('utf-8').rstrip('\x00')
        self.sig = sig.decode('utf-8').rstrip('\x00')
        # print('LoginPackage serverid: ', serverid)


class LoginResponsePackage(BasicStructPackage):
    m_cmd = 0x040002
    fmt = '!3i'
    code = 0    # 0 is successful, others is failed

    def parse(self, buffer):
        cmd, size, code = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        self.code = code


class ChatFilterPackage(BasicStructPackage):
    m_cmd = 0x040003
    fmt = '!4i'
    msgid = 0x040000
    msgsize = 0x000000
    msg = '' # max 255 char
    msgbuffer = b''

    def parse(self, buffer):
        buffer_size = struct.calcsize(self.fmt)
        _fmt_buffer = buffer[:buffer_size]
        _left_buffer = buffer[buffer_size:]

        cmd, size, msgid, msgsize = struct.unpack(self.fmt, _fmt_buffer)

        self.cmd = cmd
        self.size = size
        self.msgid = msgid
        self.msgsize = msgsize
        
        if msgsize:
            self.msgbuffer = _left_buffer[:msgsize]
        else:
            self.msgbuffer = _left_buffer
        
        try:
            self.msg = self.msgbuffer.decode('utf-8')
        except:
            logging.error('Unpack Failed :: CMD= {}, Buffer= {}'.format(cmd, _left_buffer))
            self.msg = self.msgbuffer.decode('utf-8', "ignore")


        if len(self.msg) > 255:
            self.msg = self.msg[:255]


class ChatWithJSONPackage(BasicStructPackage):
    m_cmd = 0x041003
    fmt = '!4i'
    msgid = 0x040000
    roomid = 'none'
    msg = ''
    jsonsize = 0x000000
    jsonstr = ''
    json = {}

    def parse(self, buffer):
        buffer_size = struct.calcsize(self.fmt)
        _fmt_buffer = buffer[:buffer_size]
        _left_buffer = buffer[buffer_size:]

        cmd, size, msgid, jsonsize = struct.unpack(self.fmt, _fmt_buffer)
        self.cmd = cmd
        self.size = size
        self.msgid = msgid
        self.jsonsize = jsonsize
        
        if jsonsize:
            self.jsonbuffer = _left_buffer[:jsonsize]
        else:
            self.jsonbuffer = _left_buffer
        
        try:
            self.jsonstr = self.jsonbuffer.decode('utf-8', "ignore")
            self.json = json.loads(self.jsonstr)
            self.roomid = self.json.get('roomid', 'none')
            self.msg = self.json.get('msg', '')
        except:
            self.jsonstr = self.jsonbuffer.decode('utf-8', "ignore")
            logging.error('Unpack Failed :: CMD= {}, Buffer= {}, JSON= {}'.format(cmd, _left_buffer, self.jsonstr))
            self.json = {}
            self.msg = '[Parsing Byte Failed]'


class ChatFilterResponsePackage(BasicStructPackage):
    m_cmd = 0x040004
    fmt = '!4i'
    msgid = 0x000000
    code = 0x000000 # 0:normal; 1:ads; 2:dirty words; 3:system failure

    def parse(self, buffer):
        cmd, size, msgid, code = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        self.msgid = msgid
        self.code = code


class NickNameFilterRequestPackage(BasicStructPackage):
    m_cmd = 0x040007
    fmt = '!3i'
    reqid = 0x000000
    nickname = ''

    def parse(self, buffer):
        buffer_size = struct.calcsize(self.fmt)
        _fmt_buffer = buffer[:buffer_size]
        _left_buffer = buffer[buffer_size:]

        cmd, size, reqid = struct.unpack(self.fmt, _fmt_buffer)
        _left_size = size - buffer_size
        self.cmd = cmd
        self.size = size
        self.reqid = reqid

        try:
            self.nickname = _left_buffer[:_left_size].decode('utf-8').replace("\x00", "")
        except:
            logging.error('Unpack NickNameFilterRequestPackage Failed :: CMD= {}, Buffer= {}'.format(cmd, _left_buffer))
            self.nickname = _left_buffer[:_left_size].decode('utf-8', "ignore").replace("\x00", "")


class NickNameFilterResponsePackage(BasicStructPackage):
    m_cmd = 0x040008
    fmt = '!4i'
    reqid = 0x000000
    code = 0x000000 # 0:normal; 1:ads; 2:dirty words; 3:invalid pattern; 4:system failure

    def parse(self, buffer):

        cmd, size, reqid, code = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        self.reqid = reqid
        self.code = code
