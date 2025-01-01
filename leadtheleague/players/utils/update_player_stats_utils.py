from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from setuptools import logging
from game.models import Settings
from game.utils.get_season_stats_utils import get_current_season
from players.models import PlayerMatchStatistic, PlayerMatchRating, Player, Statistic, PlayerSeasonStatistic
from teams.models import TeamPlayer, TeamTactics


def get_base_price(position_name):
    setting_name = f'{position_name}_base_price'
    try:
        return Settings.objects.get(key=setting_name).value
    except Settings.DoesNotExist:
        logging.error(f"Настройката '{setting_name}' не съществува.")
        return 100000

def get_age_factor(age):
    if 14 <= age <= 18:
        return 1.00
    elif 19 <= age <= 21:
        return 1.50
    elif 22 <= age <= 28:
        return 1.20
    elif 29 <= age <= 33:
        return 1.00
    else:
        return 0.70

def get_position_factor(position_name):
    position_factors = {
        "Goalkeeper": 1.00,
        "Defender": 1.50,
        "Midfielder": 2.00,
        "Attacker": 3.00,
    }
    return position_factors.get(position_name, 1.00)  # Стойност по подразбиране


def get_attribute_factor(player):
    total_attributes = sum(player.playerattribute_set.values_list('value', flat=True))
    if total_attributes == 0:
        return 1.0
    return 1 + total_attributes / 300


def get_statistics_factor(player, season):
    match_ratings = PlayerMatchRating.objects.filter(player=player, match__season=season).values_list('rating',
                                                                                                      flat=True)
    if not match_ratings:  # Ако няма оценки, връщаме базова стойност
        return 5.0
    average_rating = sum(match_ratings) / len(match_ratings)
    return 1 + average_rating / 10

def update_player_price(player):
    season = get_current_season()
    base_price = get_base_price(player.position.name)
    age_factor = get_age_factor(player.age)
    position_factor = get_position_factor(player.position.name)
    attribute_factor = get_attribute_factor(player)
    statistics_factor = get_statistics_factor(player, season)

    final_price = base_price * age_factor * position_factor * attribute_factor * statistics_factor
    player.price = final_price
    player.save()
    return int(final_price)


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


def release_player_from_team(user_team, player):
    team_player = get_object_or_404(TeamPlayer, team=user_team, player=player)
    team_player.delete()
    player.is_free_agent = True
    player.save()

def promoting_youth_players():
    # If players make 18 years old -> Main Team
    youth_players_ready_for_promotion = Player.objects.filter(is_youth=True, age__gte=18)
    youth_players_ready_for_promotion.update(is_youth=False)

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

    missing_stats = set(statistics_map.keys()) - set(statistics_map.keys())
    if missing_stats:
        raise ValueError(f"Липсват следните статистики в базата: {', '.join(missing_stats)}")

    season_stats_to_update = []
    new_season_stats = []

    with transaction.atomic():
        for match_stat in match_stats:
            season_stat, created = PlayerSeasonStatistic.objects.get_or_create(
                player=match_stat.player,
                statistic=match_stat.statistic,
                season=match.season,
                defaults={'value': 0}
            )

            if created:
                new_season_stats.append(season_stat)
            else:
                season_stats_to_update.append((season_stat, match_stat.value))

        for season_stat, match_value in season_stats_to_update:
            season_stat.value = F('value') + match_value
            season_stat.save()

    print(f"Season stats updated for {len(starting_players)} players.")
