from setuptools import logging

from game.models import Settings
from players.models import PlayerMatchStatistic


def update_player_price(player):
    """
    Изчислява цената на футболиста на базата на позицията му, възрастта и общите атрибути.
    """

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
    """
    Изчислява рейтингът на играч за даден мач на базата на статистически показатели и техните тежести.
    """
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match)
    stats_dict = {stat.statistic.name: stat.value for stat in stats}

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

    rating = 5.0
    for stat, weight in weights.items():
        rating += stats_dict.get(stat, 0) * weight

    return max(1.0, min(10.0, rating))
