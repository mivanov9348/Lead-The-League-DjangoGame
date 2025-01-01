from django.urls import path
from match.views import match, user_match, match_stats

app_name = 'match'

urlpatterns = [
    path('user_match', user_match, name='user_match'),
    path('match/<int:match_id>', match, name='match'),
    path('match_stats/<int:id>/', match_stats, name='match_stats')
]
