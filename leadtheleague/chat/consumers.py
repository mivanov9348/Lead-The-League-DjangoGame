import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = f"chat_{self.user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        sender = self.user
        receiver = await database_sync_to_async(User.objects.get)(id=data["receiver_id"])
        message = await database_sync_to_async(Message.objects.create)(
            sender=sender, receiver=receiver, text=data["text"]
        )

        response = {
            "sender_id": sender.id,
            "sender_username": sender.username,
            "receiver_id": receiver.id,
            "text": message.text,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

        await self.channel_layer.group_send(
            f"chat_{receiver.id}",
            {"type": "chat_message", "message": response},
        )

        await self.send(text_data=json.dumps(response))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
