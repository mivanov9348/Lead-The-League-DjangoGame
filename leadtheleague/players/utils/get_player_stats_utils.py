from django.db.models import Prefetch, Avg
from game.models import Season
from players.models import Player, PlayerSeasonStatistic


def get_player_team(player):
    player = Player.objects.prefetch_related('team_players__team').get(id=player.id)
    team_player = player.team_players.first()  # Взима първия запис от TeamPlayer
    return {
        'team_name': team_player.team.name if team_player else 'No team',
        'shirt_number': team_player.shirt_number if team_player else None,
    }


def get_personal_player_data(player):
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
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    attributes = {}
    for attr in player.playerattribute_set.all():
        attributes[attr.attribute.name] = attr.value
    return attributes


def get_player_season_stats(player, season=None):
    query = player.season_stats.select_related('season', 'statistic')
    if season:
        query = query.filter(season=season)
    stats = {}
    for stat in query:
        stats[stat.statistic.name] = {
            'value': stat.value,
            'rating': stat.rating,
        }
    return stats


def get_player_season_stats_all_seasons(player):
    seasons = Season.objects.all().order_by("-season_number")
    all_stats = {}
    for season in seasons:
        all_stats[season.season_number] = get_player_season_stats(player, season)
    return all_stats


def get_players_season_stats_by_team(team):
    players = team.team_players.select_related('player').prefetch_related('player__season_stats')

    player_data = {}
    for team_player in players:
        player = team_player.player
        season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('statistic')
        stats_dict = {}
        for stat in season_stats:
            stats_dict[stat.statistic.name] = {
                'value': stat.value,
                'rating': stat.rating,
            }
        player_rating = season_stats.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        player_data[player.id] = {
            'personal_info': {
                'name': player.name,
                'position': player.position.name,
            },
            'season_stats': stats_dict,
            'rating': player_rating,
        }
    return player_data


def get_player_data(player):
    return {
        'personal_info': get_personal_player_data(player),
        'attributes': get_player_attributes(player),
        'team_info': get_player_team(player),
        'stats': {
            'season_stats': get_player_season_stats(player),
            'match_stats': get_player_match_stats(player),
        },
    }

def get_player_match_stats(player, match=None):
    query = player.match_stats.select_related('match', 'statistic')
    if match:
        query = query.filter(match=match)
    match_stats = {}
    for stat in query:
        match_id = stat.match.id
        if match_id not in match_stats:
            match_stats[match_id] = {}
        match_stats[match_id][stat.statistic.name] = stat.value
    return match_stats