from django.urls import path
from . import views

urlpatterns = [
    path('teams/', views.team_list, name='team_list'),
    path('teams/squad', views.team_squad, name='team_squad'),
    path('teams/line-up', views.line_up, name='line_up'),
    path('teams/team-stats', views.team_stats, name='team_stats'),
    path('teams/delete/<int:team_id>', views.delete_team, name='delete_team')
]
