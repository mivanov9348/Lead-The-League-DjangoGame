import json

from django.db import models
import pandas as pd
from game.models import Season
from players.models import PlayerSeasonStatistic, PlayerSeasonAnalytics
from django.db.models import Sum


def calculate_player_points(stats, weights):
    points = 0

    for stat, value in stats.items():
        weight = weights.get(stat.lower(), 0)
        points += value * weight

    matches = stats.get('Matches', 0)
    points += matches * 0.1

    goals = stats.get('Goals', 0)
    assists = stats.get('Assists', 0)
    shoots = stats.get('Shoots', 0)
    yellow_cards = stats.get('YellowCards', 0)
    red_cards = stats.get('RedCards', 0)

    points += goals * 2
    points += assists * 1

    if shoots > 0 and goals > 0:
        shooting_efficiency = goals / shoots
        if shooting_efficiency < 0.2:
            points -= (1 - shooting_efficiency) * 3

    points -= yellow_cards * 1
    points -= red_cards * 2

    return round(points, 2)

def update_season_analytics():
    """Актуализира статистиките на играчите за активния сезон."""
    weights = {
        'Assists': 3,
        'CleanSheets': 5,
        'Conceded': -2,
        'Dribbles': 2,
        'Fouls': -1,
        'Goals': 4,
        'Matches': 1,
        'Passes': 1,
        'RedCards': -5,
        'Saves': 4,
        'Shoots': 2,
        'ShootsOnTarget': 2.5,
        'Tackles': 2,
        'YellowCards': -3,
    }

    active_seasons = Season.objects.filter(is_active=True)

    for season in active_seasons:
        aggregated_stats = (
            PlayerSeasonStatistic.objects.filter(season=season)
            .values('player_id')
            .annotate(
                Assists=Sum('value', filter=models.Q(statistic__name='Assists')),
                CleanSheets=Sum('value', filter=models.Q(statistic__name='CleanSheets')),
                Conceded=Sum('value', filter=models.Q(statistic__name='Conceded')),
                Dribbles=Sum('value', filter=models.Q(statistic__name='Dribbles')),
                Fouls=Sum('value', filter=models.Q(statistic__name='Fouls')),
                Goals=Sum('value', filter=models.Q(statistic__name='Goals')),
                Matches=Sum('value', filter=models.Q(statistic__name='Matches')),
                Passes=Sum('value', filter=models.Q(statistic__name='Passes')),
                RedCards=Sum('value', filter=models.Q(statistic__name='RedCards')),
                Saves=Sum('value', filter=models.Q(statistic__name='Saves')),
                Shoots=Sum('value', filter=models.Q(statistic__name='Shoots')),
                ShootsOnTarget=Sum('value', filter=models.Q(statistic__name='ShootsOnTarget')),
                Tackles=Sum('value', filter=models.Q(statistic__name='Tackles')),
                YellowCards=Sum('value', filter=models.Q(statistic__name='YellowCards')),
            )
        )

        analytics = []
        for stats in aggregated_stats:
            player_id = stats.pop('player_id')
            points = calculate_player_points(stats, weights)

            analytics.append(PlayerSeasonAnalytics(
                player_id=player_id,
                season=season,
                points=points,
                statistics=stats
            ))

        PlayerSeasonAnalytics.objects.filter(season=season).delete()
        PlayerSeasonAnalytics.objects.bulk_create(analytics)
