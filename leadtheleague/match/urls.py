from django.urls import path,re_path
from match.views import match, next_event, user_match
from . import consumers

app_name = 'match'

urlpatterns = [
    path('match/user_match', user_match, name='user_match'),
    path('match/<int:match_id>', match, name='match'),
    path('next_event/', next_event, name='next_event'),
]

websocket_urlpatterns = [
    re_path(r'ws/match/(?P<match_id>\d+)/$', consumers.LiveScoreConsumer.as_asgi()),
]