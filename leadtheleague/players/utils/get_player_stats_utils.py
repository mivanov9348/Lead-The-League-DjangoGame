import random

from django.db.models import Prefetch, QuerySet, Avg
from game.utils.get_season_stats_utils import get_current_season
from players.models import Player, PlayerSeasonStatistic, Position, Attribute, PlayerMatchRating, PlayerAttribute
from players.utils.generate_player_utils import generate_random_player
from teams.models import TeamPlayer, Team


def get_all_positions() -> QuerySet[Position]:
    return Position.objects.all()


def get_average_player_rating_for_current_season(player: Player) -> float:
    # Получаваме текущия сезон
    current_season = get_current_season()

    # Изчисляваме средния рейтинг за играча за текущия сезон
    average_rating = PlayerMatchRating.objects.filter(
        player=player,
        match__season=current_season  # Предполага се, че атрибутът 'season' е наличен
    ).aggregate(Avg('rating'))['rating__avg']

    return average_rating if average_rating is not None else 0.0


def get_player_team(player):
    team_player = player.team_players.select_related('team').first()
    return {
        'id': team_player.team.id if team_player else 'No Team',
        'team_name': team_player.team.name if team_player else 'No teams',
        'shirt_number': team_player.shirt_number if team_player else None,
        'team_logo': team_player.team.logo.url if team_player else None,
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
        'image_url': player.image.url if player.image else None,

    }


def get_player_attributes(player):
    """Retrieve all attributes for a given player."""
    attributes = PlayerAttribute.objects.filter(player=player).select_related('attribute')
    return [
        {
            'name': attr.attribute.name,
            'value': attr.value,
            'progress': attr.progress,
        }
        for attr in attributes
    ]


def get_player_season_stats(player, season=None):
    query = player.season_stats.select_related('season', 'statistic')
    if season:
        query = query.filter(season=season)
    return {stat.statistic.name: stat.value for stat in query}


def get_player_season_stats_all_seasons(player):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('season', 'statistic')

    # Групираме статистиките по сезони
    all_stats = {}
    for stat in season_stats:
        season_number = stat.season.season_number
        if season_number not in all_stats:
            all_stats[season_number] = {}
        all_stats[season_number][stat.statistic.name] = stat.value

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
                'id': player.id,
                'name': player.name,
                'age': player.age,
                'position': player.position.name if player.position else 'Unknown',
                'position_abbr': player.position.abbreviation if player.position else 'N/A',
                'nationality': player.nationality.name if player.nationality else 'Unknown',
                'nationality_abbr': player.nationality.abbreviation if player.nationality else 'N/A',
                'image_url': player.image.url if player.image else None,
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
    query = player.match_stats.select_related('match')

    if match:
        query = query.filter(match=match)

    match_stats = {}
    for stat in query:
        match_id = stat.match.id
        if match_id not in match_stats:
            match_stats[match_id] = {}
        for key, value in stat.statistics.items():
            match_stats[match_id][key] = value

    return match_stats


def get_all_free_agents():
    players = Player.objects.filter(is_free_agent=True).prefetch_related(
        Prefetch(
            'playerattribute_set',
            queryset=PlayerAttribute.objects.select_related('attribute'),
            to_attr='attributes'
        )
    )
    for player in players:
        player.attributes = {
            attr.attribute.name: attr.value for attr in player.attributes
        }
    return players


def get_all_youth_players_by_team(team):
    """Retrieve all youth players from a specific teams along with their attributes."""
    youth_players = team.team_players.filter(
        player__is_youth=True
    ).select_related('player__position', 'player__nationality', 'team')

    youth_players_data = []
    for team_player in youth_players:
        player = team_player.player

        attributes_data = get_player_attributes(player)

        youth_players_data.append({
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
            'image': player.image.url if player.image else None,
            'potential': player.potential_rating,
            'attributes': attributes_data,  # Добавяне на атрибутите към играча
        })

    return youth_players_data

def ensure_all_teams_has_minimum_players():
    teams = Team.objects.all()
    for team in teams:
        ensure_team_has_minimum_players(team)

def ensure_team_has_minimum_players(team):
    required_positions = {
        "Goalkeeper": 1,
        "Defender": 4,
        "Midfielder": 4,
        "Forward": 2,
    }

    # Fetch current players by position
    team_players = TeamPlayer.objects.filter(team=team).select_related("player")
    position_count = {pos: 0 for pos in required_positions.keys()}

    for team_player in team_players:
        position_name = team_player.player.position.name
        if position_name in position_count:
            position_count[position_name] += 1

    # Generate random players for missing positions
    for position_name, required_count in required_positions.items():
        missing_count = required_count - position_count.get(position_name, 0)
        if missing_count > 0:
            position = Position.objects.filter(name=position_name).first()
            for _ in range(missing_count):
                generate_random_player(team=team, position=position)

    # Ensure there are 11 total players
    current_player_count = team_players.count()
    if current_player_count < 11:
        additional_players_needed = 11 - current_player_count
        all_positions = list(Position.objects.all())
        for _ in range(additional_players_needed):
            random_position = random.choice(all_positions)
            generate_random_player(team=team, position=random_position)

    return f"Team '{team.name}' now has at least 11 players with the required positions."
