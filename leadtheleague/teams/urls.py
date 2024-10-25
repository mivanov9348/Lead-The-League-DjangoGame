from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('create_team/', views.create_team, name='create_team'),
    path('squad/', views.team_squad, name='team_squad'),
    path('line-up/', views.line_up, name='line_up'),
    path('line-up/save', views.save_lineups, name='save_lineups'),
    path('team-stats/', views.team_stats, name='team_stats'),
]
