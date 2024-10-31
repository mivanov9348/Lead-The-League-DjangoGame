from django.urls import path
from inbox.views import inbox

app_name = 'inbox'

urlpatterns = [
    path('inbox/', inbox, name='inbox')
]
