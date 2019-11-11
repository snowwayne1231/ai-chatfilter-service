from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
# from django.conf import settings
import json

from ai.apps import MainAiApp
import numpy

ai_app = MainAiApp()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        # async_to_sync(self.channel_layer.group_add)(
        #     self.room_group_name,
        #     self.channel_name
        # )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        print('== connected ==')

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # print('receive message :', message)

        if message:
            prediction = ai_app.predict(str(message))
        else:
            prediction = -1
        # print('prediction :', prediction)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'prediction': int(prediction),
            }
        )

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))

    async def chat_message(self, event):
        message = event['message']
        prediction = event['prediction']

        await self.send(text_data=json.dumps({
            'message': message,
            'prediction': prediction
        }))

    