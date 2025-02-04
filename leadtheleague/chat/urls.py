from django.urls import path
from .views import chat, send_message, get_messages

app_name = 'chat'

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('send/', send_message, name='send_message'),
    path('messages/<int:receiver_id>/', get_messages, name='get_messages'),
]
