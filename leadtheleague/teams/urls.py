from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('create_team/', views.create_team, name='create_team'),
    path('teams/', views.team_list, name='team_list'),
    path('squad/', views.team_squad, name='team_squad'),
    path('line-up/', views.line_up, name='line_up'),
    path('team-stats/', views.team_stats, name='team_stats'),
]
