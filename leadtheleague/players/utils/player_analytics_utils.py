import json

from django.db import models
import pandas as pd
from game.models import Season
from players.models import PlayerSeasonStatistic, PlayerSeasonAnalytics
from django.db.models import Sum

def calculate_player_points(stats, weights):
    points = 0
    matches = stats.get('Matches', 1) or 1

    for stat, value in stats.items():
        weight = weights.get(stat.lower(), 0)
        points += value * weight

    points += stats.get('Goals', 0) / matches * 10
    points += stats.get('Assists', 0) / matches * 7
    points -= stats.get('YellowCards', 0) * 3
    points -= stats.get('RedCards', 0) * 5

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
        'MinutesPlayed': 0.5,
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
                MinutesPlayed=Sum('value', filter=models.Q(statistic__name='MinutesPlayed')),
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


def export_to_csv():
    analytics = PlayerSeasonAnalytics.objects.all()

    # Преобразуване към списък от речници
    data = [
        {
            'player_id': item.player.id,
            'season_id': item.season.id,
            'points': item.points,
            'statistics': json.dumps(item.statistics),  # Преобразуване в JSON формат
        }
        for item in analytics
    ]

    # Създаване на DataFrame
    df = pd.DataFrame(data)

    # Записване като CSV
    df.to_csv('player_season_analytics.csv', index=False)

def panda_analyze():
    df = pd.read_csv('player_season_analytics.csv')

    # Разгръщане на колоната `statistics`
    stats_df = pd.json_normalize(df['statistics'])
    combined_df = pd.concat([df.drop(columns=['statistics']), stats_df], axis=1)

    # Преглед на резултатите
    print(combined_df.head())

    avg_points = combined_df.groupby('player_id')['points'].mean()
    print(avg_points)

    top_players = combined_df.nlargest(10, 'points')
    print(top_players)
