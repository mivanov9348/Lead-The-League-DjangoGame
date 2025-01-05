from django.urls import path
from match.views import match_stats

app_name = 'match'

urlpatterns = [
    path('match_stats/<int:id>/', match_stats, name='match_stats'),
]
