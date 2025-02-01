import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

from leadtheleague.consumers import ChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leadtheleague.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/chat/<str:username>/", ChatConsumer.as_asgi()),
        ])
    ),
})