import json

from django.db import models
import pandas as pd
from game.models import Season
from players.models import PlayerSeasonStatistic, PlayerSeasonAnalytics
from django.db.models import Sum

def calculate_player_points(stats, weights):
    points = 0
    matches = stats.get('matches', 1) or 1  # Избягване на деление на нула

    for stat, value in stats.items():
        weight = weights.get(stat.lower(), 0)
        points += value * weight

    points += stats.get('goals', 0) / matches * 10
    points += stats.get('assists', 0) / matches * 7
    points -= stats.get('yellowcards', 0) * 3
    points -= stats.get('redcards', 0) * 5

    return round(points, 2)

def update_season_analytics():
    """Актуализира статистиките на играчите за активния сезон."""
    weights = {
        'assists': 3,
        'cleansheets': 5,
        'conceded': -2,
        'dribbles': 2,
        'fouls': -1,
        'goals': 4,
        'matches': 1,
        'minutesplayed': 0.5,
        'passes': 1,
        'redcards': -5,
        'saves': 4,
        'shoots': 2,
        'shootsontarget': 2.5,
        'tackles': 2,
        'yellowcards': -3,
    }

    # Получаване на текущия активен сезон
    active_seasons = Season.objects.filter(is_active=True)

    for season in active_seasons:
        aggregated_stats = (
            PlayerSeasonStatistic.objects.filter(season=season)
            .values('player_id')
            .annotate(
                assists=Sum('value', filter=models.Q(statistic__name='Assists')),
                cleansheets=Sum('value', filter=models.Q(statistic__name='CleanSheets')),
                conceded=Sum('value', filter=models.Q(statistic__name='Conceded')),
                dribbles=Sum('value', filter=models.Q(statistic__name='Dribbles')),
                fouls=Sum('value', filter=models.Q(statistic__name='Fouls')),
                goals=Sum('value', filter=models.Q(statistic__name='Goals')),
                matches=Sum('value', filter=models.Q(statistic__name='Matches')),
                minutesplayed=Sum('value', filter=models.Q(statistic__name='MinutesPlayed')),
                passes=Sum('value', filter=models.Q(statistic__name='Passes')),
                redcards=Sum('value', filter=models.Q(statistic__name='RedCards')),
                saves=Sum('value', filter=models.Q(statistic__name='Saves')),
                shoots=Sum('value', filter=models.Q(statistic__name='Shoots')),
                shootsontarget=Sum('value', filter=models.Q(statistic__name='ShootsOnTarget')),
                tackles=Sum('value', filter=models.Q(statistic__name='Tackles')),
                yellowcards=Sum('value', filter=models.Q(statistic__name='YellowCards')),
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
                statistics=stats  # Запис на агрегирани статистики в JSON поле
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
