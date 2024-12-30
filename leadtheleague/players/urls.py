from django.urls import path
from .views import player_profile, youth_academy, sign_player, free_agents, \
    submit_offer, \
    get_free_agent_info, release_player, all_players

app_name = 'players'

urlpatterns = [
    path('all_players/', all_players, name='all_players'),
    path('youth_academy/', youth_academy, name='youth_academy'),
    path('player_profile/<int:player_id>', player_profile, name='player_profile'),
    path('sign/<int:player_id>/', sign_player, name='sign_player'),
    path('<int:player_id>/release/',release_player, name='release_player'),
    path('free_agents', free_agents, name='free_agents'),
    path('<int:player_id>/info/', get_free_agent_info, name='get_free_agent_info'),
    path('<int:player_id>/offer/', submit_offer, name='submit_offer'),
]
