from django.db import transaction
from django.db.models import Avg, Prefetch
import random
from game.utils.get_season_stats_utils import get_current_season
from game.utils.settings_utils import get_setting_value
from players.models import Position, PlayerMatchRating, PlayerAttribute, PlayerSeasonStatistic, Player, \
    PlayerMatchStatistic, PositionAttribute
from players.utils.generate_player_utils import generate_random_player, calculate_player_potential
from teams.models import TeamPlayer, Team, TeamTactics


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
    return [
        {
            'name': attr.attribute.name,
            'value': attr.value,
            'progress': attr.progress,
            'progress_percent': (attr.progress / 10.0) * 100,  # Прогрес в проценти за визуализация
        }
        for attr in attributes
    ]


def get_player_match_stats(match, team):
    try:
        team_tactics = TeamTactics.objects.get(team=team)
        starting_players = team_tactics.starting_players.all()
    except TeamTactics.DoesNotExist:
        return []

    player_stats = PlayerMatchStatistic.objects.filter(match=match, player__in=starting_players)

    stats_list = []
    for stat in player_stats:
        stats = {
            'player': stat.player,
            'matches': stat.statistics.get('Matches', 0),
            'assists': stat.statistics.get('Assists', 0),
            'clean_sheets': stat.statistics.get('CleanSheets', 0),
            'conceded': stat.statistics.get('Conceded', 0),
            'dribbles': stat.statistics.get('Dribbles', 0),
            'fouls': stat.statistics.get('Fouls', 0),
            'goals': stat.statistics.get('Goals', 0),
            'passes': stat.statistics.get('Passes', 0),
            'red_cards': stat.statistics.get('RedCards', 0),
            'saves': stat.statistics.get('Saves', 0),
            'shoots': stat.statistics.get('Shoots', 0),
            'shoots_on_target': stat.statistics.get('ShootsOnTarget', 0),
            'tackles': stat.statistics.get('Tackles', 0),
            'yellow_cards': stat.statistics.get('YellowCards', 0),
        }
        stats_list.append(stats)

    return stats_list


def get_player_season_stats_all_seasons(player):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('season', 'statistic')

    all_stats = {}
    for stat in season_stats:
        season_number = stat.season.season_number
        if season_number not in all_stats:
            all_stats[season_number] = {}
        all_stats[season_number][stat.statistic.name] = stat.value

    return all_stats


def get_current_season_stats(player):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('season', 'statistic').order_by(
        '-season__year')

    if not season_stats.exists():
        return None

    latest_season = season_stats.first().season.year
    latest_stats = season_stats.filter(season__year=latest_season)

    stats = {}
    for stat in latest_stats:
        stats[stat.statistic.name] = stat.value

    return stats


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
    """Format a single player's data for DataTables."""
    attributes = {
        attr.attribute.name.lower(): attr.value for attr in player.relevant_attributes
    }
    return {
        'id': player.id,
        'name': player.name,
        'age': player.age,
        'nationality': player.nationality.name if player.nationality else "-",
        'nationalityabbr': player.nationality.abbreviation if player.nationality else "-",
        'team': player.team_players.first().team.name if player.team_players.exists() else "Free Agent",
        'position': player.position.abbreviation if player.position else "-",
        'agent': f"{player.agent.first_name} {player.agent.last_name}" if player.agent else "No Agent",
        **attributes,
        'price': player.price,
        'potential_rating': round(player.potential_rating, 2),
        'is_free_agent': player.is_free_agent,

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

        season_rating = PlayerMatchRating.objects.filter(
            player=player,
            match__season=season
        ).aggregate(Avg('rating')).get('rating__avg', 0.0) or 0.0

        player_data[player.id] = {
            'personal_info': get_personal_player_data(player),
            'season_stats': season_stats,
            'season_rating': round(season_rating, 2),  # Закръгляме до 2 знака след десетичната запетая
        }
    return player_data


def get_all_players():
    return Player.objects.select_related(
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
            'is_free_agent': team_player.player.is_free_agent
        }
        for team_player in youth_players
    ]


def ensure_all_teams_has_minimum_players():
    for team in Team.objects.all():
        ensure_team_has_minimum_players(team)


def ensure_team_has_minimum_players(team, season):
    required_positions = {
        "Goalkeeper": get_setting_value("minimum_goalkeepers_by_team"),
        "Defender": get_setting_value("minimum_defenders_by_team"),
        "Midfielder": get_setting_value("minimum_midfielders_by_team"),
        "Forward": get_setting_value("minimum_attackers_by_team"),
    }

    team_players = TeamPlayer.objects.filter(team=team).select_related("player")
    position_count = {pos: 0 for pos in required_positions.keys()}

    for team_player in team_players:
        position_name = team_player.player.position.name
        if position_name in position_count:
            position_count[position_name] += 1

    with transaction.atomic():
        for position_name, required_count in required_positions.items():
            missing_count = required_count - position_count.get(position_name, 0)
            if missing_count > 0:
                position = Position.objects.filter(name=position_name).first()
                for _ in range(missing_count):
                    player = generate_random_player(team=team, position=position)
                    player.age = random.randint(14, 17)
                    player.is_youth = True
                    player.potential_rating = calculate_player_potential(player)
                    player.season = season
                    player.save()

        current_player_count = team_players.count()
        team_minimum_players = get_setting_value("team_minimum_players")
        if current_player_count < team_minimum_players:
            additional_players_needed = team_minimum_players - current_player_count
            all_positions = list(Position.objects.all())
            for _ in range(additional_players_needed):
                random_position = random.choice(all_positions)
                player = generate_random_player(team=team, position=random_position)
                player.age = random.randint(get_setting_value('youth_player_minimum_age'),
                                            get_setting_value('youth_player_maximum_age'))
                player.is_youth = True
                player.potential_rating = calculate_player_potential(player)
                player.season = season
                player.save()

    return f"Team '{team.name}' now has at least 11 players with the required positions."


def ensure_all_teams_within_maximum_players():
    for team in Team.objects.all():
        if not ensure_team_within_maximum_players(team):
            return False
    return True


def ensure_team_within_maximum_players(team):
    MAX_PLAYERS = get_setting_value("team_maximum_players")

    total_players = TeamPlayer.objects.filter(team=team).count()

    if total_players > MAX_PLAYERS:
        print(f"Error: Team '{team.name}' exceeds the maximum allowed players ({MAX_PLAYERS}).")
        return False

    return True


def calculate_player_rating(player):
    position = player.position
    if not position:
        raise ValueError(f"Player {player.name} does not have a defined position.")

    position_attributes = PositionAttribute.objects.filter(position=position)
    player_attributes = PlayerAttribute.objects.filter(player=player)

    rating = 0

    for pos_attr in position_attributes:
        player_attr = player_attributes.filter(attribute=pos_attr.attribute).first()
        if player_attr:
            rating += pos_attr.importance * player_attr.value

    return rating


def get_top_players_from_list(players):
    if not players:
        raise ValueError("No agents provided to determine the top player.")

    best_player = None
    highest_rating = -1

    for player in players:
        rating = calculate_player_rating(player)
        if rating > highest_rating:
            highest_rating = rating
            best_player = player

    if best_player:
        return best_player.name

    raise ValueError("Unable to determine the top player from the provided agents.")
