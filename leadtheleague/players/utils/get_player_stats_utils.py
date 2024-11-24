from collections import defaultdict

from django.db.models import Prefetch

from game.models import Season
from game.utils import get_current_season
from players.models import PlayerMatchStatistic, Player, PlayerSeasonStatistic
from teams.models import TeamPlayer


def get_player_team(player):
    player = Player.objects.prefetch_related('team_players__team').get(id=player.id)
    team_player = player.team_players.first()  # Взима първия запис от TeamPlayer
    return {
        'team_name': team_player.team.name if team_player else 'No team',
        'shirt_number': team_player.shirt_number if team_player else None,
    }


def get_personal_player_data(player):
    """
    Връща основната персонална информация за един играч.
    """
    return {
        'id': player.id,
        'name': player.name,
        'first_name': player.first_name,
        'last_name': player.last_name,
        'position': player.position.name if player.position else 'Unknown',
        'nationality': player.nationality.name if player.nationality else 'Unknown',
        'age': player.age,
        'price': player.price,
        'is_active': player.is_active,
        'is_youth': player.is_youth,
        'is_free_agent': player.is_free_agent,
    }


def get_player_attributes(player):
    """
    Връща атрибутите на даден играч.
    """
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}


def get_player_season_stats(player, season=None):
    query = player.season_stats.select_related('season', 'statistic')
    if season:
        query = query.filter(season=season)
    return {
        stat.statistic.name: {
            "value": stat.value,
            "rating": stat.rating
        }
        for stat in query
    }


def get_player_season_stats_all_seasons(player):
    """
    Метод за извличане на всички статистики на играча за всички сезони.

    :param player: Играчът, за който се вземат статистиките.
    :return: Речник със статистики на играча за всеки сезон.
    """
    seasons = Season.objects.all().order_by("-season_number")
    all_stats = {}

    for season in seasons:
        season_stats = get_player_season_stats(player, season)
        all_stats[season.season_number] = season_stats

    return all_stats


def get_players_season_stats_by_team(team):
    """
    Извлича сезонната статистика за всички играчи от даден отбор за текущия сезон.
    """
    season = get_current_season()

    # Вземаме играчи от отбора с предварително заредени статистики
    team_players = TeamPlayer.objects.filter(team=team).select_related(
        'player'
    ).prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.filter(season=season).select_related('statistic'),
            to_attr='season_stats_for_team'
        )
    )

    players_stats = []

    for team_player in team_players:
        player = team_player.player
        season_stats = player.season_stats_for_team if hasattr(player, 'season_stats_for_team') else []

        players_stats.append({
            'personal_info': get_personal_player_data(player),
            'season_stats': [
                {
                    'statistic': stat.statistic.name,
                    'value': stat.value,
                    'rating': stat.rating
                } for stat in season_stats
            ],
            'team': team.name
        })

    return players_stats


def get_player_data(player):
    """
    Връща пълната информация за даден играч.
    """
    personal_info = get_personal_player_data(player)
    attributes = get_player_attributes(player)
    team_info = get_player_team(player)
    season_stats = get_player_season_stats(player)
    match_stats = get_player_match_stats(player)

    return {
        'personal_info': personal_info,
        'attributes': attributes,
        'team_info': team_info.team_name,
        'stats': {
            'season_stats': season_stats,
            'match_stats': match_stats,
        },
    }


def get_player_match_stats(player, match=None):
    query = player.match_stats.select_related('match', 'statistic')
    if match:
        query = query.filter(match=match)
    return {
        stat.match.id: {
            stat.statistic.name: stat.value
            for stat in query.filter(match=stat.match)
        }
        for stat in query
    }
