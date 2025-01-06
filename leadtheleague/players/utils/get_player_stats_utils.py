from django.db.models import Avg, Prefetch
import random

from game.utils.get_season_stats_utils import get_current_season
from players.models import Position, PlayerMatchRating, PlayerAttribute, PlayerSeasonStatistic, Player
from players.utils.generate_player_utils import generate_random_player
from teams.models import TeamPlayer, Team


def get_all_positions():
    return Position.objects.all()

def get_average_player_rating_for_current_season(player):
    current_season = get_current_season()
    return PlayerMatchRating.objects.filter(
        player=player,
        match__season=current_season
    ).aggregate(Avg('rating')).get('rating__avg', 0.0) or 0.0

def get_player_team(player):
    team_player = player.team_players.select_related('team').first()
    if team_player:
        return {
            'id': team_player.team.id,
            'team_name': team_player.team.name,
            'shirt_number': team_player.shirt_number,
            'team_logo': team_player.team.logo.url if team_player.team.logo else None,
        }
    return {
        'id': None,
        'team_name': 'No Team',
        'shirt_number': None,
        'team_logo': None,
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
    attributes = PlayerAttribute.objects.filter(player=player).select_related('attribute')
    return {
        attr.attribute.name: attr.value for attr in attributes
    }

def get_player_season_stats_all_seasons(player):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('season', 'statistic')

    all_stats = {}
    for stat in season_stats:
        season_number = stat.season.season_number
        if season_number not in all_stats:
            all_stats[season_number] = {}
        all_stats[season_number][stat.statistic.name] = stat.value

    return all_stats

def get_player_stats(player, season=None, match=None):
    stats = {}

    if season:
        season_stats = player.season_stats.filter(season=season).select_related('statistic')
        stats['season_stats'] = {stat.statistic.name: stat.value for stat in season_stats}

    if match:
        match_stats = player.match_stats.filter(match=match).select_related('match')
        stats['match_stats'] = {
            stat.match.id: stat.statistics for stat in match_stats
        }

    return stats

def get_player_data(player, season=None, match=None):
    return {
        'personal_info': get_personal_player_data(player),
        'attributes': get_player_attributes(player),
        'team_info': get_player_team(player),
        'stats': get_player_stats(player, season=season, match=match),
    }

def format_player_data(player):
    """Format a single player's data for frontend usage."""
    attributes = {
        attr.attribute.name.lower(): attr.value for attr in player.relevant_attributes
    }
    return {
        'id': player.id,
        'name': player.name,
        'age': player.age,
        'nationality': player.nationality.name if player.nationality else "-",
        'nationalityabbr': player.nationality.abbreviation if player.nationality else "-",
        'position': player.position.name if player.position else "-",
        'positionabbr': player.position.abbreviation if player.position else "-",
        'agent': f"{player.agent.first_name} {player.agent.last_name}" if player.agent else "No Agent",
        **attributes,
        'price': player.price,
        'image_url': player.image
    }

def get_players_season_stats_by_team(team, season):
    players = team.team_players.select_related('player').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.filter(season=season).select_related('statistic')
        )
    )
    player_data = {}
    for team_player in players:
        player = team_player.player
        season_stats = {
            stat.statistic.name: stat.value for stat in player.season_stats.filter(season=season)
        }
        player_data[player.id] = {
            'personal_info': get_personal_player_data(player),
            'season_stats': season_stats,
        }
    return player_data

def get_all_free_agents():
    return Player.objects.filter(is_free_agent=True).select_related(
        'nationality', 'position', 'agent'
    ).prefetch_related(
        Prefetch(
            'playerattribute_set',
            queryset=PlayerAttribute.objects.filter(
                attribute__name__in=[
                    'Handling', 'Reflexes', 'Finishing', 'Shooting', 'Technique',
                    'Passing', 'Crossing', 'Tackling', 'Strength', 'Determination',
                    'BallControl', 'Dribbling', 'Speed', 'Vision', 'WorkRate'
                ]
            ).select_related('attribute'),
            to_attr='relevant_attributes'
        )
    )


def get_all_youth_players_by_team(team):
    youth_players = team.team_players.filter(player__is_youth=True).select_related(
        'player__position', 'player__nationality'
    )

    return [
        {
            'id': team_player.player.id,
            'name': f"{team_player.player.first_name} {team_player.player.last_name}",
            'first_name': team_player.player.first_name,
            'last_name': team_player.player.last_name,
            'position': team_player.player.position.name if team_player.player.position else 'Unknown',
            'positionabbr': team_player.player.position.abbreviation if team_player.player.position else 'Unknown',
            'nationality': team_player.player.nationality.name if team_player.player.nationality else 'Unknown',
            'nationalityabbr': team_player.player.nationality.abbreviation if team_player.player.nationality else 'Unknown',
            'age': team_player.player.age,
            'price': team_player.player.price,
            'image': team_player.player.image.url if team_player.player.image else None,
            'potential': team_player.player.potential_rating,
            'attributes': get_player_attributes(team_player.player),
        }
        for team_player in youth_players
    ]

def ensure_team_has_minimum_players(team):
    required_positions = {
        "Goalkeeper": 1,
        "Defender": 4,
        "Midfielder": 4,
        "Forward": 2,
    }

    team_players = TeamPlayer.objects.filter(team=team).select_related("player")
    position_count = {pos: 0 for pos in required_positions.keys()}

    for team_player in team_players:
        position_name = team_player.player.position.name
        if position_name in position_count:
            position_count[position_name] += 1

    for position_name, required_count in required_positions.items():
        missing_count = required_count - position_count.get(position_name, 0)
        if missing_count > 0:
            position = Position.objects.filter(name=position_name).first()
            for _ in range(missing_count):
                generate_random_player(team=team, position=position)

    current_player_count = team_players.count()
    if current_player_count < 11:
        additional_players_needed = 11 - current_player_count
        all_positions = list(Position.objects.all())
        for _ in range(additional_players_needed):
            random_position = random.choice(all_positions)
            generate_random_player(team=team, position=random_position)

    return f"Team '{team.name}' now has at least 11 players with the required positions."

def ensure_all_teams_has_minimum_players():
    for team in Team.objects.all():
        ensure_team_has_minimum_players(team)
