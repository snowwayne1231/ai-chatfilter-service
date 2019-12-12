import struct



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

    elif cmd == ChatFilterResponsePackage.m_cmd:

        msgid = options.get('msgid', 0x000000)
        code = options.get('code', 0x000000)

        size = struct.calcsize(ChatFilterResponsePackage.fmt)
        package = struct.pack(ChatFilterResponsePackage.fmt, cmd, size, msgid, code)
    

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

    elif cmd == ChatFilterResponsePackage.m_cmd:

        return ChatFilterResponsePackage(buffer)
    

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
    msgtxt = '' # max 100 char
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
        self.msgbuffer = _left_buffer
        

        try:
            self.msgtxt = _left_buffer.decode('utf-8').rstrip('\x00')
        except:
            print('>>>>> Unpack Error msgid: ', msgid, ' | left_buffer: ', _left_buffer)
            _left_buffer = _left_buffer[:msgsize]
            self.msgbuffer = _left_buffer
            self.msgtxt = _left_buffer.decode('utf-8', "ignore").rstrip('\x00')



class ChatFilterResponsePackage(BasicStructPackage):
    m_cmd = 0x040004
    fmt = '!4i'
    msgid = 0x000000
    code = 0x000000 # 0 is pass

    def parse(self, buffer):
        cmd, size, msgid, code = struct.unpack(self.fmt, buffer)
        self.cmd = cmd
        self.size = size
        self.msgid = msgid
        self.code = code