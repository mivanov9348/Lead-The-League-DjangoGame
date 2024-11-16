from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('create_team/', views.create_team, name='create_team'),
    path('squad/', views.squad, name='squad'),
    path('line_up/', views.line_up, name='line_up'),
    path('add_starting_player/', views.add_starting_player, name='add_starting_player'),
    path('remove-starting-player/', views.remove_starting_player, name='remove_starting_player'),
    path('select_tactics/', views.select_tactics, name='select_tactics'),
    path('team-stats/', views.team_stats, name='team_stats'),
]
