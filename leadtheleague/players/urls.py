from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('all_players/', views.all_players, name='all_players')
]
