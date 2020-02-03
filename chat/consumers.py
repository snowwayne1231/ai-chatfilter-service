from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from service.main import MainService

# from django.conf import settings
import json

main_service = MainService()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        # self.room_group_name = 'chat_%s' % self.room_name
        self.room_group_name = 'chatting_filter'
        # async_to_sync(self.channel_layer.group_add)(
        #     self.room_group_name,
        #     self.channel_name
        # )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        print('== Consumer connected ==')

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        msgid = text_data_json.get('msgid', None)
        message = text_data_json.get('message', None)
        user = text_data_json.get('user', None)
        room = text_data_json.get('room', None)
        detail = text_data_json.get('detail', False)

        if message:
            
            results = main_service.think(message=message, user=user, room=room, detail=detail)
            
        else:
            results = {
                'message': message,
                'prediction': 0,
            }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': user, 
                'room': room,
                'msgid': msgid,
                'message': results.get('message', ''),
                'prediction': int(results.get('prediction', 0)),
                'reason_char': results.get('reason_char', ''),
                'detail': results.get('detail', {}),
            }
        )

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))

    async def chat_message(self, event):
        msgid = event['msgid']
        message = event['message']
        prediction = event['prediction']
        reason_char = event['reason_char']
        user = event['user']
        room = event['room']
        detail = event['detail']

        await self.send(text_data=json.dumps({
            'msgid': msgid,
            'message': message,
            'prediction': prediction,
            'reason_char': reason_char,
            'user': user,
            'room': room,
            'detail': detail,
        }))

    