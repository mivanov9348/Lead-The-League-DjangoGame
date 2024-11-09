from django.urls import path
from match.views import match, next_event, user_match

app_name = 'match'

urlpatterns = [
    path('match/user_match', user_match, name='user_match'),
    path('match/<int:match_id>', match, name='match'),
    path('next_event/', next_event, name='next_event'),
]
