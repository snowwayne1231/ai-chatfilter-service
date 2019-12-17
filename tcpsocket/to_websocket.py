import time, sys, getopt, json
import websocket
import threading
# from multiprocessing.connection import Listener
from multiprocessing.pool import ThreadPool
# import asyncio


WS_URL =  "ws://127.0.0.1:{}/ws/chat/"
# websocket.enableTrace(True)



class WebsocketThread (threading.Thread):

    _name = ''
    _port = 80
    _url = ''
    _waitting_ids = []
    _message_result = dict()

    stop_event = None
    ws = None
    loop = None


    def __init__(self, name = 'default', port = 80):
        threading.Thread.__init__(self)
        self._name = name
        self._port = port
        self._url = WS_URL.format(port)
        self.stop_event = threading.Event()
        self.pool = ThreadPool(processes=4)
    

    def run(self):
        self.on_start()


    def on_start(self):
        
        self.ws = websocket.WebSocketApp(self._url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    
    def on_open(self):
        print('Web Socket Client opened.')

    
    def send_thread(self, data):
        _msg_id = data.get('msgid')
        self._waitting_ids.append(_msg_id)
        
        _str = json.dumps(data)
        # print('send _str: ', _str)
        self.ws.send(_str)

        #
        while _msg_id in self._waitting_ids:
            pass
            # print('whileing _msg_id: ', _msg_id)
            # time.sleep(0.1)
        
        _res = self._message_result.pop(_msg_id)
        return _res


    def on_message(self, message):
        # print('on_message', message)
        _json = json.loads(message)
        _msg_id = _json.get('msgid', None)
        # print('on_message msgid: ', _msg_id)
        if _msg_id:
            self._message_result.update({_msg_id: _json})
            self._waitting_ids.remove(_msg_id)

    def on_error(self, error):
        print('Web Socket Error: ', error, flush=True)

    def on_close(self):
        print("### Web Socket Closed ###", flush=True)
        

    def stop(self):
        self.stop_event.set()
        self.ws.close()


    def stopped(self):
        return self.stop_event.is_set()

    
    def thinking(self, msg, msgid, room='none', user='none'):
        _data = {
            'message':msg,
            'msgid':msgid,
            'room':room,
            'user':user,
        }
        print('thinking start run!!')
        
        async_result = self.pool.apply_async(self.send_thread, [_data])
        
        values = async_result.get()

        print('thinking end!! ... values: ', values)
        
        return values

