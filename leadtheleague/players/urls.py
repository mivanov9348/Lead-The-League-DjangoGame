from django.urls import path
from . import views
from .views import player_profile, send_offer, youth_academy

app_name = 'players'

urlpatterns = [
    path('all_players/', views.all_players, name='all_players'),
    path('youth_academy/', youth_academy, name='youth_academy'),
    path('player_profile/<int:player_id>', player_profile, name='player_profile'),
    path('release/<int:player_id>/', views.release_player, name='release_player'),
    path('sign/<int:player_id>/', views.sign_player, name='sign_player'),
    path('send_offer/', send_offer, name='send_offer'),
]
