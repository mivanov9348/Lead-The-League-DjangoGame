from game.models import Season
from players.models import PlayerSeasonStatistic, Player, PlayerSeasonAnalytics


def calculate_season_player_points(stats, weights):
    points = 0
    matches = stats.get('matches', 1)

    for stat_name, value in stats.items():
        weight = weights.get(stat_name.lower(), 0)
        points += value * weight

    if matches > 0:
        points += stats.get('goals', 0) / matches * 10
        points += stats.get('assists', 0) / matches * 7
        points -= stats.get('yellowcards', 0) * 3
        points -= stats.get('redcards', 0) * 5

    return round(points, 2)

def update_season_analytics():
    weights = {
        'goals': 4,
        'assists': 3,
        'matches': 1,
        'minutesplayed': 0.5,
        'shoots': 2,
        'shootsontarget': 2.5,
        'passes': 1,
        'dribbles': 2,
        'tackles': 2,
        'cleansheets': 5,
        'saves': 4,
        'fouls': -1,
        'conceded': -2,
        'yellowcards': -3,
        'redcards': -5,
    }

    seasons = Season.objects.filter(is_active=True)
    for season in seasons:
        player_stats = (
            PlayerSeasonStatistic.objects.filter(season=season)
            .select_related('player', 'statistic')
        )

        analytics = {}
        for stat in player_stats:
            player_id = stat.player.id
            if player_id not in analytics:
                analytics[player_id] = {}
            analytics[player_id][stat.statistic.name] = analytics[player_id].get(stat.statistic.name, 0) + stat.value

        for player_id, stats in analytics.items():
            player = Player.objects.get(id=player_id)
            points = calculate_season_player_points(stats, weights)

            PlayerSeasonAnalytics.objects.update_or_create(
                player=player,
                season=season,
                defaults={
                    'points': points,
                    'statistics': stats,
                }
            )