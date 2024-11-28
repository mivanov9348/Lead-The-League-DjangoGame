from setuptools import logging

from game.models import Settings
from players.models import PlayerMatchStatistic, PlayerMatchRating

"""Calculate player price"""
def update_player_price(player):

    def get_base_price(position_name):
        setting_name = f'{position_name}_Base_Price'
        try:
            return Settings.objects.get(name=setting_name).value
        except Settings.DoesNotExist:
            logging.error(f"Настройката '{setting_name}' не съществува.")
            return 100000  # Стойност по подразбиране

    DEFAULT_BASE_PRICE = 100000

    def get_age_factor(age):
        if age < 25:
            return 1.2
        elif age > 30:
            return 0.8
        return 1.0

    base_price = get_base_price(player.position.name) or DEFAULT_BASE_PRICE
    age_factor = get_age_factor(player.age)
    total_attributes = sum(player.playerattribute_set.values_list('value', flat=True))

    return int(base_price * age_factor + total_attributes * 10000)

# updatestats
def update_player_rating(player, match):
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match).select_related('statistic')

    # Тежести за статистиките
    weights = {
        'assists': 1.0,
        'cleanSheets': 1.5,
        'conceded': -1.0,
        'dribbles': 0.5,
        'fouls': -0.5,
        'goals': 2.0,
        'matches': 0.1,
        'minutesPlayed': 0.01,
        'passes': 0.2,
        'redCards': -2.0,
        'saves': 1.0,
        'shoots': 0.3,
        'shootsOnTarget': 0.5,
        'tackles': 0.3,
        'yellowCards': -0.5,
    }

    base_rating = 5.0
    total_weighted_score = 0
    stats_count = 0

    # Изчисляване на общия принос от статистиките
    for stat in stats:
        weight = weights.get(stat.statistic.name, 0)
        total_weighted_score += stat.value * weight
        stats_count += 1

    # Изчисляване на финалния рейтинг
    if stats_count > 0:
        rating = base_rating + (total_weighted_score / (1 + stats_count))
    else:
        rating = base_rating

    # Ограничаваме рейтинга между 1.0 и 10.0
    rating = max(1.0, min(10.0, rating))

    # Създаваме или обновяваме записа в PlayerMatchRating
    match_rating, created = PlayerMatchRating.objects.update_or_create(
        player=player,
        match=match,
        defaults={'rating': rating}
    )

    return rating