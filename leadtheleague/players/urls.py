from django.urls import path
from . import views
from .views import player_profile, send_offer

app_name = 'players'

urlpatterns = [
    path('all_players/', views.all_players, name='all_players'),
    path('player_profile/<int:player_id>', player_profile, name='player_profile'),
    path('send_offer/', send_offer, name='send_offer'),
]
