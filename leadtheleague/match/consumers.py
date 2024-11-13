# match/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LiveScoreConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Създаване на канал, свързан със специфичен мач или група
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f"match_{self.match_id}"

        # Присъединяване към група
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Напускане на групата
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Получаване на съобщение от WebSocket (не е задължително тук)
        pass

    # Метод за изпращане на резултатите в реално време
    async def send_score(self, event):
        score = event['score']
        time = event.get('time', '00:00')  # ако има време, го включи
        await self.send(text_data=json.dumps({
            'score': score,
            'time': time,
        }))
