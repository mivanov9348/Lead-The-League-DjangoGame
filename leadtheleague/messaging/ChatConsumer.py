import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from accounts.models import CustomUser
from messaging.models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['username']  # Името на получателя
        self.room_group_name = f'chat_{self.room_name}'  # Групата на чата

        # Присъединяване към групата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()  # Приемане на WebSocket връзката

    async def disconnect(self, close_code):
        # Излизане от групата
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_username = data['sender']

        # Получаване на изпращача и получателя
        sender = await database_sync_to_async(CustomUser.objects.get)(username=sender_username)
        recipient = await database_sync_to_async(CustomUser.objects.get)(username=self.room_name)

        # Запис на съобщението в базата данни
        await database_sync_to_async(ChatMessage.objects.create)(
            sender=sender,
            recipient=recipient,
            content=message
        )

        # Изпращане на съобщението в групата
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Изпращане на съобщението през WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))
