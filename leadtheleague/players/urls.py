from django.urls import path

from .api import players_list_api
from .views import player_profile, youth_academy, sign_player, submit_offer, get_free_agent_info, release_player, \
    all_players, top_league_players, search_players, api_search_players

app_name = 'players'

urlpatterns = [
    path('all_players/', all_players, name='all_players'),
    path('top_league_players/', top_league_players, name='top_league_players'),  # Без параметър
    path('top_league_players/<int:league_id>/', top_league_players, name='top_league_players_with_id'),
    path('api/players/', players_list_api, name='players_list_api'),
    path('youth_academy/', youth_academy, name='youth_academy'),
    path('player_profile/<int:player_id>/', player_profile, name='player_profile'),
    path('sign/<int:player_id>/', sign_player, name='sign_player'),
    path('<int:player_id>/release/',release_player, name='release_player'),

    path('search_players', search_players, name='search_players'),
    path('api/search-players/', api_search_players, name='api_search_players'),

    path('<int:player_id>/info/', get_free_agent_info, name='get_free_agent_info'),
    path('<int:player_id>/offer/', submit_offer, name='submit_offer'),
]
