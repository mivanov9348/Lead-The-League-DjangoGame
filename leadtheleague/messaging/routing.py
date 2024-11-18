# messaging/routing.py
from django.urls import path

from messaging.ChatConsumer import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:username>/', ChatConsumer.as_asgi()),
]