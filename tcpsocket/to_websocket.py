import time, sys, getopt, json
import websocket
import threading
# from multiprocessing.connection import Listener
from multiprocessing.pool import ThreadPool
# import asyncio
import logging
# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d | %I:%M:%S %p :: ', level=logging.DEBUG)

WS_URL =  "ws://{}:{}/ws/chat/"
# websocket.enableTrace(True)



class WebsocketThread (threading.Thread):

    _name = ''
    _port = 80
    _url = ''
    _waitting_ids = []
    _message_result = dict()

    stop_event = None
    ws = None
    pool = None
    is_active = False
    second_warn_spend_time = 0.35
    tcp_potokey = '__tcp__'


    def __init__(self, name = 'default', host = '0.0.0.0', port = 80):
        threading.Thread.__init__(self)
        self._name = name
        self._port = port
        self._url = WS_URL.format(host, port)
        self.stop_event = threading.Event()
        self.pool = ThreadPool(processes=4)
    

    def run(self):
        self.on_start()


    def on_start(self):
        # print('on start: ', self._url)
        self.ws = websocket.WebSocketApp(self._url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        self.ws.on_open = self.on_open
        
        
        while True:
            if self.stopped():
                break
            self.ws.run_forever(ping_interval=10, ping_timeout=2)
            time.sleep(3)

    
    def on_open(self):
        logging.info('Web Socket Connection opened.')
        self.is_active = True
        self.setting()

    
    def send_thread(self, data):
        _msg_id = data.get('msgid', None)
        _limted_timeout = 1
        _now = time.time()
        _res = {}
        #
        if _msg_id:

            # print('send_thread: ', data)
            if isinstance(_msg_id, int):
                self._waitting_ids.append(_msg_id)

            _str = json.dumps(data)
            # logging.debug('Web Socket Send Thread ID: {}'.format(_msg_id))
            self.ws.send(_str)
            # _gap = 0

            # while _msg_id in self._waitting_ids:
                
            #     _gap = time.time() - _now
                
            #     if _gap > _limted_timeout:
            #         logging.error('### Web Socket Timeout.. msgid:[ {} ]'.format(_msg_id))
            #         if _msg_id in self._waitting_ids:
            #             self._waitting_ids.remove(_msg_id)
            #         break

            #     time.sleep(0.002)

            # if self._message_result.get(_msg_id, None):

            #     _res = self._message_result.pop(_msg_id)

            #     if _gap > self.second_warn_spend_time:
            #         logging.warning('# Web Socket Slow Warning By Data: {}'.format(_str))

        else:

            logging.info('Web Socket No Need Think [without msg id].')

        return _res


    def on_message(self, message):
        # print('on_message', message)
        _json = json.loads(message)
        _msg_id = _json.get('msgid', None)
        
        if _msg_id and _msg_id in self._waitting_ids:
            self._waitting_ids.remove(_msg_id)
        elif _msg_id != self.tcp_potokey:
            logging.debug('Web Socket on_message recive unknown msgid: {}'.format(message))

        # self._message_result.update({_msg_id: _json})
        

    def on_error(self, error):
        logging.error('### Web Socket Error: {}'.format(error))
        self.is_active = False
        self._waitting_ids = []
        self._message_result = dict()
        # raise Exception(error)


    def on_close(self):
        self.is_active = False
        logging.warning("# Web Socket Closed ###")
        

    def stop(self):
        self.is_active = False
        self.stop_event.set()
        self.ws.close()


    def stopped(self):
        return self.stop_event.is_set()


    def setting(self):
        return self.pool.apply(self.send_thread, [{'tcp': True, 'msgid': self.tcp_potokey}])

    
    def send_msg(self, msgid, msg, room='', user='', prediction=0):
        _data = {
            'message':msg,
            'msgid':msgid,
            'room':room,
            'user':user,
            'prediction': prediction,
        }
        # print('thinking start run!!')

        values = self.pool.apply(self.send_thread, [_data])

        # print('thinking end!! ... values: ', values)
        
        return values

