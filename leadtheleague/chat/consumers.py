from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Message
from django.contrib.auth import get_user_model

from .utils.cryptography_utils import encrypt_message, decrypt_message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"chat_{min(self.user.id, int(self.other_user_id))}_{max(self.user.id, int(self.other_user_id))}"
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        sender = self.user
        receiver = await database_sync_to_async(User.objects.get)(id=data["receiver_id"])

        encrypted_text = encrypt_message(data["text"])
        print(f"Encrypted: {encrypted_text}")  # Debug

        message = await database_sync_to_async(Message.objects.create)(
            sender=sender, receiver=receiver, encrypted_text=encrypted_text
        )

        decrypted_text = decrypt_message(message.encrypted_text)
        print(f"Decrypted: {decrypted_text}")  # Debug

        response = {
            "sender_id": sender.id,
            "sender_username": sender.username,
            "receiver_id": receiver.id,
            "text": decrypted_text,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": response},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
