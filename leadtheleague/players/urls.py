from django.urls import path
from .views import player_profile, youth_academy, sign_player, release_player, all_players, free_agents_2

app_name = 'players'

urlpatterns = [
    path('all_players/', all_players, name='all_players'),
    path('youth_academy/', youth_academy, name='youth_academy'),
    path('player_profile/<int:player_id>', player_profile, name='player_profile'),
    path('release/<int:player_id>/', release_player, name='release_player'),
    path('sign/<int:player_id>/', sign_player, name='sign_player'),
    path('free_agents_2', free_agents_2, name='free_agents_2')
]
