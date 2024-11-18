from django.urls import path
from .views import create_team, squad, team_stats, line_up, lineup_add_player, lineup_remove_player

app_name = 'teams'

urlpatterns = [
    path('create_team/', create_team, name='create_team'),
    path('squad/', squad, name='squad'),
    path("line_up/", line_up, name="line_up"),
    path("lineup/add-player/", lineup_add_player, name="lineup_add_player"),
    path("lineup/remove-player/", lineup_remove_player, name="lineup_remove_player"),
    path('team-stats/', team_stats, name='team_stats'),
]
