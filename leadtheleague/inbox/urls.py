from django.urls import path
from inbox.views import  send_message, inbox_view, view_message

app_name = 'inbox'

urlpatterns = [
    path('inbox/inbox_view/', inbox_view, name='inbox_view'),
    path('inbox/send/', send_message, name='send_message'),
    path('inbox/view_message/<int:id>/', view_message, name='view_message'),
]
