from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from service import instance

# from django.conf import settings
import json
from service.widgets import printt




class ChatConsumer(AsyncWebsocketConsumer):
    """

    """

    main_service = None
    hostname = None
    is_tcp = False
    is_standby = True
    group_name_global = 'GLOBAL_CHATTING'
    group_name_standby = 'GLOBAL_CHATTING_STATNDBY'
    # max_message_length = 255
    key_get_pinyin_data = '__getpinyindata__'
    key_send_train_remotely = '__remotetrain__'


    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        # self.group_name_global = 'chat_%s' % self.room_name
        # async_to_sync(self.channel_layer.group_add)(
        #     self.group_name_global,
        #     self.channel_name
        # )

        self.main_service = instance.get_main_service(is_admin=True)
        if not self.main_service.is_open_mind:
            self.main_service.open_mind()

        await self.channel_layer.group_add(
            self.group_name_global,
            self.channel_name
        )

        print('== Consumer connected == channel_name: ', self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name_global,
            self.channel_name
        )

        if self.is_tcp and self.is_standby:
            await self.channel_layer.group_discard(
                self.group_name_standby,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        is_setting_tcp = text_data_json.get('tcp', False)
        msgid = text_data_json.get('msgid', None)
        message = text_data_json.get('message', None)
        result_next = {
            'type': 'chat_message',
            'msgid': msgid,
            'message': message,
            # 'reason_char': results.get('reason_char', ''),
        }
        
        printt('receive: ', text_data_json)

        if is_setting_tcp:
            self.is_tcp = True
            self.hostname = text_data_json.get('hostname', None)
            if self.hostname:
                self.is_standby = True
                await self.channel_layer.group_add(
                    self.group_name_standby,
                    self.channel_name
                )


        elif message and isinstance(msgid, int):
            user = text_data_json.get('user', None)
            room = text_data_json.get('room', None)
            detail = text_data_json.get('detail', False)

            if detail:
                
                results = self.main_service.think(message=message, room=room, detail=detail)
                result_next.update(results)
                # printt('websocket ai think: ', results)
            else:
                prediction = text_data_json.get('prediction', 0)
                result_next['prediction'] = prediction
                
            
            self.main_service.saveRecord(result_next['prediction'], message=message)
            printt('Save Message: {} | {}'.format(message, result_next['prediction']))
        
        elif isinstance(msgid, str):
            message = self.get_message_by_order(msgid)
            __break__ = self.do_something_by_order(msgid, message)
            if __break__:
                return False
            result_next['message'] = message
            
        # print('consumer result_next: ', result_next)

        await self.channel_layer.group_send(
            self.group_name_global,
            result_next,
            # {
            #     'type': 'chat_message',
            #     'user': user, 
            #     'room': room,
            #     'msgid': msgid,
            #     'message': message,
            #     'prediction': int(results.get('prediction', 0)),
            #     'reason_char': results.get('reason_char', ''),
            #     'detail': results.get('detail', {}),
            # }
        )
        

    async def chat_message(self, event):
        msgid = event['msgid']
        message = event['message']
        type_msg = type(msgid)

        if self.is_tcp:
            
            if type_msg is int:
                await self.send(text_data=json.dumps({
                    'msgid': msgid,
                    # 'prediction': prediction,
                }))
            elif type_msg is str:
                await self.send(text_data=json.dumps({
                    'msgid': msgid,
                    'message': message,
                }))
        else:
            # admin
            if type_msg is int:
                prediction = int(event.get('prediction', 0))
                reason_char = event.get('reason_char', '')
                user = event.get('user', '')
                room = event.get('room', 'none')
                detail = event.get('detail', {})
                await self.send(text_data=json.dumps({
                    'msgid': msgid,
                    'message': message,
                    'prediction': prediction,
                    'reason_char': reason_char,
                    'user': user,
                    'room': room,
                    'detail': detail,
                }))
            elif type_msg is str:
                await self.send(text_data=json.dumps({
                    'msgid': msgid,
                    'message': message,
                }))
            

    async def send_cmd_start_train(self, event):
        message = event.get('message', None)
        print('[send_cmd_start_train] message: ', message)
        print('[send_cmd_start_train] self.hostname: ', self.hostname)
    

    def get_message_by_order(self, order_key):
        if order_key == self.key_get_pinyin_data:
            return self.main_service.get_pinyin_data()
        elif order_key == self.key_send_train_remotely:
            return self.main_service.get_train_textbook()
        
        return None


    def do_something_by_order(self, order_key, message):
        _should_break = False
        if order_key == self.key_send_train_remotely:
            print('[do_something_by_order] self.hostname: ', self.hostname)
            self.channel_layer.group_send(
                self.group_name_standby,
                {
                    'type': 'send_cmd_start_train',
                    'message': message,
                },
            )
            _should_break = True

        return _should_break

    