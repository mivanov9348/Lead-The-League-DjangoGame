from django.urls import path
from .ChatConsumer import ChatConsumer

websocket_urlpatterns = [
    path('ws/messaging/chat/<str:username>/', ChatConsumer.as_asgi()),
]