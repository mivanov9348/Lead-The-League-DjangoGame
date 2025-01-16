from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import messaging.routing
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leadtheleague.settings')

# Настройка на ASGI приложение
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # За HTTP заявки
    "websocket": AuthMiddlewareStack(  # За WebSocket
        URLRouter(
            messaging.routing.websocket_urlpatterns  # Свързване с маршрутизаторите за WebSocket
        )
    ),
})