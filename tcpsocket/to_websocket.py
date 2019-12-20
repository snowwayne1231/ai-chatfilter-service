import time, sys, getopt, json
import websocket
import threading
# from multiprocessing.connection import Listener
from multiprocessing.pool import ThreadPool
# import asyncio
import logging
# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d | %I:%M:%S %p :: ', level=logging.DEBUG)

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
    pool = None


    def __init__(self, name = 'default', port = 80):
        threading.Thread.__init__(self)
        self._name = name
        self._port = port
        self._url = WS_URL.format(port)
        self.stop_event = threading.Event()
        self.pool = ThreadPool(processes=2)
    

    def run(self):
        self.on_start()


    def on_start(self):
        
        self.ws = websocket.WebSocketApp(self._url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        self.ws.on_open = self.on_open
        
        
        while True:
            if self.stopped():
                break
            self.ws.run_forever(ping_interval=10, ping_timeout=5)

    
    def on_open(self):
        logging.info('Web Socket Connection opened.')

    
    def send_thread(self, data):
        _msg_id = data.get('msgid')
        _limted_timeout = 2
        _now = time.time()
        #
        if _msg_id:

            self._waitting_ids.append(_msg_id)
            _str = json.dumps(data)
            logging.debug('Web Socket send thread data: {}'.format(_str))
            self.ws.send(_str)

            while _msg_id in self._waitting_ids:
                # print('whileing _msg_id: ', _msg_id)
                # time.sleep(1)
                _gap = time.time() - _now
                # logging.debug('_gap: {}'.format(_gap))
                if _gap > _limted_timeout:
                    logging.error('### Web Socket Timeout.. msgid:[ {} ]'.format(_msg_id))
                    if _msg_id in self._waitting_ids:
                        self._waitting_ids.remove(_msg_id)
                    break

                time.sleep(0.02)
            
            if self._message_result.get(_msg_id):

                _res = self._message_result.pop(_msg_id)

            else:

                _res = {}

        else:

            logging.info('Web Socket no need think [without msg id].')
            _res = {}

        return _res


    def on_message(self, message):
        # print('on_message', message)
        _json = json.loads(message)
        _msg_id = _json.get('msgid', None)
        logging.debug('Web Socket on_message: {}'.format(message))
        if _msg_id and _msg_id in self._waitting_ids:
            self._waitting_ids.remove(_msg_id)
            self._message_result.update({_msg_id: _json})
        else:
            pass

    def on_error(self, error):
        logging.error('### Web Socket Error: {}'.format(error))
        self._waitting_ids = []
        self._message_result = dict()
        # raise Exception(error)


    def on_close(self):
        logging.warning("# Web Socket Closed ###")
        

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
        # print('thinking start run!!')

        values = self.pool.apply(self.send_thread, [_data])

        # print('thinking end!! ... values: ', values)
        
        return values
