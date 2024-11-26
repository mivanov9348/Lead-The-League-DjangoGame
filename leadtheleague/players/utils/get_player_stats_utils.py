from django.db.models import Prefetch, Avg, QuerySet
from game.models import Season
from players.models import Player, PlayerSeasonStatistic, Position, Nationality


def get_all_nationalities() -> QuerySet[Nationality]:
    """Retrieve all nationalities from the database."""
    return Nationality.objects.all()


def get_all_positions() -> QuerySet[Position]:
    """Retrieve all positions from the database."""
    return Position.objects.all()


def get_player_team(player):
    player = Player.objects.prefetch_related('team_players__team').get(id=player.id)
    team_player = player.team_players.first()
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
        'positionabbr': player.position.abbreviation if player.position else 'Unknown',
        'nationality': player.nationality.name if player.nationality else 'Unknown',
        'nationalityabbr': player.nationality.abbreviation if player.nationality else 'Unknown',
        'age': player.age,
        'price': player.price,
        'is_active': player.is_active,
        'is_youth': player.is_youth,
        'is_free_agent': player.is_free_agent,
    }


def get_player_attributes(player):
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}


def get_player_season_stats(player, season=None):
    query = player.season_stats.select_related('season', 'statistic')
    if season:
        query = query.filter(season=season)
    return {stat.statistic.name: stat.value for stat in query}


def get_player_season_stats_all_seasons(player):
    seasons = Season.objects.prefetch_related(
        Prefetch(
            'playerseasonstatistic_set',
            queryset=PlayerSeasonStatistic.objects.filter(player=player).select_related('statistic')
        )
    ).order_by('-season_number')

    all_stats = {}
    for season in seasons:
        stats = {stat.statistic.name: stat.value for stat in season.playerseasonstatistic_set.all()}
        all_stats[season.season_number] = stats
    return all_stats


def get_players_season_stats_by_team(team):
    players = team.team_players.select_related('player').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        )
    )
    player_data = {}
    for team_player in players:
        player = team_player.player
        season_stats = {
            stat.statistic.name: stat.value for stat in player.season_stats.all()
        }
        player_data[player.id] = {
            'personal_info': {
                'name': player.name,
                'position': player.position.name,
            },
            'season_stats': season_stats,
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


def get_all_free_agents():
    free_agents = Player.objects.filter(is_free_agent=True).prefetch_related('playerattribute_set__attribute')
    free_agents_data = []
    for player in free_agents:
        attributes = {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}
        free_agents_data.append({
            'id': player.id,
            'name': player.name,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'position': player.position.name if player.position else 'Unknown',
            'positionabbr': player.position.abbreviation if player.position else 'Unknown',
            'nationality': player.nationality.name if player.nationality else 'Unknown',
            'nationalityabbr': player.nationality.abbreviation if player.nationality else 'Unknown',
            'age': player.age,
            'price': player.price,
            'attributes': attributes,
        })

    return free_agents_data
