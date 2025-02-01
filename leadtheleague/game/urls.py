from django.urls import path
from .views import get_teams_by_league_api, home, choose_team, mark_notifications_as_viewed, get_unread_notifications, \
    get_game_state, calendar, match_schedule

app_name = 'game'

urlpatterns = [
    path('home/', home, name='home'),
    path('api/teams/<int:league_id>/', get_teams_by_league_api, name='get_teams_by_league_api'),
    path('choose_team/', choose_team, name='choose_team'),
    path('get_unread_notifications/', get_unread_notifications, name='get_unread_notifications'),
    path('mark_notifications_as_viewed/', mark_notifications_as_viewed, name='mark_notifications_as_viewed'),
    path('get_game_state/', get_game_state, name='get_game_state'),

    path('calendar/', calendar, name='calendar'),
    path('api/match-schedule/<int:season_id>/', match_schedule, name='match_schedule')

]
