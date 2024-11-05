from django.urls import path
from match.views import match, next_event

app_name = 'match'

urlpatterns = [
    path('match/', match, name='match'),
    path('next_event/', next_event, name='next_event'),
]
