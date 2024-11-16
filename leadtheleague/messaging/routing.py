from django.urls import path
from messaging import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:username>/', ChatConsumer.as_asgi()),
]
