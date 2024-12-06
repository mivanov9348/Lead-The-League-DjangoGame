from django.urls import path
from .views import  get_teams_by_league_api, home, choose_team

app_name = 'game'

urlpatterns = [
    path('home/', home, name='home'),
    path('api/teams/<int:league_id>/', get_teams_by_league_api, name='get_teams_by_league_api'),
    path('choose_team/',choose_team, name='choose_team'),
]
