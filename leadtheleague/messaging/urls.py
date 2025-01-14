from django.urls import path
from messaging.views import inbox_view, chat_view, get_chat_messages, message_detail, delete_notification, mark_as_read

app_name = 'messaging'

urlpatterns = [
    path('chat_view/', chat_view, name='chat_view'),
    path('get-chat-messages/<int:user_id>/', get_chat_messages, name='get_chat_messages'),
    path('inbox_view/', inbox_view, name='inbox_view'),
    path('message/<int:id>/', message_detail, name='message_detail'),
    path('inbox_view/delete/<int:id>/', delete_notification, name='delete_notification'),
    path('mark-as-read/<int:message_id>/', mark_as_read, name='mark_as_read'),

]

