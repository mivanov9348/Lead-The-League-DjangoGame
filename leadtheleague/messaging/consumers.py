import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['username']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        print(f"WebSocket connected for {self.room_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(f"WebSocket disconnected for {self.room_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_username = data['sender']

        print(f"Received message from {sender_username}: {message}")

        await self.save_message(sender_username, self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    @sync_to_async
    def save_message(self, sender_username, recipient_username, message):
        sender = User.objects.get(username=sender_username)
        recipient = User.objects.get(username=recipient_username)
        ChatMessage.objects.create(
            sender=sender,
            recipient=recipient,
            content=message
        )