from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from setuptools import logging
from game.models import Settings
from game.utils.get_season_stats_utils import get_current_season
from players.models import PlayerMatchStatistic, PlayerMatchRating, Player, Statistic, PlayerSeasonStatistic
from teams.models import TeamPlayer, TeamTactics


def get_base_price(position_name):
    setting_name = f'{position_name}_base_price'
    return Settings.objects.filter(key=setting_name).values_list('value', flat=True).first() or 100000

def get_age_factor(age):
    age_factors = {
        (14, 18): 1.00,
        (19, 21): 1.50,
        (22, 28): 1.20,
        (29, 33): 1.00,
    }
    for (min_age, max_age), factor in age_factors.items():
        if min_age <= age <= max_age:
            return factor
    return 0.70

def get_position_factor(position_name):
    return {
        "Goalkeeper": 1.00,
        "Defender": 1.50,
        "Midfielder": 2.00,
        "Attacker": 3.00,
    }.get(position_name, 1.00)

def get_attribute_factor(player):
    total_attributes = player.playerattribute_set.aggregate(total=Sum('value'))['total'] or 0
    return 1 + total_attributes / 300 if total_attributes else 1.0

def get_statistics_factor(player, season):
    match_ratings = PlayerMatchRating.objects.filter(player=player, match__season=season).values_list('rating', flat=True)
    if not match_ratings:
        return 5.0
    average_rating = sum(match_ratings) / len(match_ratings)
    return 1 + average_rating / 10

def update_player_price(player):
    season = get_current_season()
    final_price = (
        get_base_price(player.position.name) *
        get_age_factor(player.age) *
        get_position_factor(player.position.name) *
        get_attribute_factor(player) *
        get_statistics_factor(player, season)
    )
    player.price = final_price
    player.save()
    return int(final_price)

def update_player_rating(player, match):
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match).select_related('statistic')

    weights = {
        'assists': 1.0, 'cleanSheets': 1.5, 'conceded': -1.0, 'dribbles': 0.5,
        'fouls': -0.5, 'goals': 2.0, 'matches': 0.1, 'minutesPlayed': 0.01,
        'passes': 0.2, 'redCards': -2.0, 'saves': 1.0, 'shoots': 0.3,
        'shootsOnTarget': 0.5, 'tackles': 0.3, 'yellowCards': -0.5,
    }

    base_rating = 5.0
    total_weighted_score = sum(stat.value * weights.get(stat.statistic.name, 0) for stat in stats)
    stats_count = len(stats)

    rating = base_rating + (total_weighted_score / (1 + stats_count)) if stats_count > 0 else base_rating
    rating = max(1.0, min(10.0, rating))

    PlayerMatchRating.objects.update_or_create(
        player=player,
        match=match,
        defaults={'rating': rating}
    )
    return rating

def release_player_from_team(user_team, player):
    team_player = get_object_or_404(TeamPlayer, team=user_team, player=player)
    team_player.delete()
    player.is_free_agent = True
    player.save()

def promoting_youth_players():
    Player.objects.filter(is_youth=True, age__gte=18).update(is_youth=False)

def all_players_age_up():
    Player.objects.update(age=F('age') + 1)

def update_season_stats_from_match(match):
    home_tactics = TeamTactics.objects.filter(team=match.home_team).first()
    away_tactics = TeamTactics.objects.filter(team=match.away_team).first()

    if not home_tactics or not away_tactics:
        raise ValueError("Не са намерени тактики за един от отборите.")

    starting_players = list(home_tactics.starting_players.all()) + list(away_tactics.starting_players.all())

    match_stats = PlayerMatchStatistic.objects.filter(match=match, player__in=starting_players)

    statistics_map = {stat.name: stat for stat in Statistic.objects.all()}

    with transaction.atomic():
        for match_stat in match_stats:
            season_stat, created = PlayerSeasonStatistic.objects.get_or_create(
                player=match_stat.player,
                statistic=match_stat.statistic,
                season=match.season,
                defaults={'value': 0}
            )
            if not created:
                season_stat.value = F('value') + match_stat.value
                season_stat.save()

    print(f"Season stats updated for {len(starting_players)} players.")
