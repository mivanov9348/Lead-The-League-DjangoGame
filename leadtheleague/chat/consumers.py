import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Message
from channels.db import database_sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"chat_{min(self.user.id, int(self.other_user_id))}_{max(self.user.id, int(self.other_user_id))}"
        self.room_group_name = f"chat_{self.room_name}"
        print(f"[WebSocket] User {self.user.id} connected to {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    async def disconnect(self, close_code):
        print(f"[WebSocket] User {self.user.id} disconnected.")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    async def receive(self, text_data):
        print(f"[WebSocket] Received: {text_data}")
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
            self.room_group_name,
            {"type": "chat_message", "message": response},
        )
    async def chat_message(self, event):
        print(f"[WebSocket] Sending: {event['message']}")
        await self.send(text_data=json.dumps(event["message"]))