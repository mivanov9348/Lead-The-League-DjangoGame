from django.urls import path
from messaging.views import inbox_view, chat_view, get_chat_messages

app_name = 'messaging'

urlpatterns = [
    path('chat_view/', chat_view, name='chat_view'),
    path('get-chat-messages/<int:user_id>/', get_chat_messages, name='get_chat_messages'),
    path('inbox_view/', inbox_view, name='inbox_view'),
]
