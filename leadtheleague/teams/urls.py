from django.urls import path
from .views import create_team, squad, team_stats, line_up, modify_lineup

app_name = 'teams'

urlpatterns = [
    path('create_team/', create_team, name='create_team'),
    path('squad/', squad, name='squad'),
    path('line_up/', line_up, name='line_up'),
    path('modify_lineup/', modify_lineup, name='modify_lineup'),

    path('team-stats/', team_stats, name='team_stats'),
]
