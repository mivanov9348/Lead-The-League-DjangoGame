from collections import defaultdict

from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from game.models import Settings
from game.utils.get_season_stats_utils import get_current_season
from players.models import PlayerMatchStatistic, PlayerMatchRating, Player, Statistic, PlayerSeasonStatistic
from teams.models import TeamPlayer, TeamTactics
from transfers.models import Transfer


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
    return next((factor for (min_age, max_age), factor in age_factors.items() if min_age <= age <= max_age), 0.70)


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
    match_ratings = PlayerMatchRating.objects.filter(player=player, match__season=season).values_list('rating',
                                                                                                      flat=True)
    if not match_ratings:
        return 5.0
    average_rating = sum(match_ratings) / len(match_ratings)
    return 1 + average_rating / 10


def update_all_players_prices():
    all_players = Player.objects.all()
    for player in all_players:
        update_player_price(player)


def update_player_price(player):
    season = get_current_season()
    final_price = (
            get_base_price(player.position.name)
            * get_age_factor(player.age)
            * get_position_factor(player.position.name)
            * get_attribute_factor(player)
            * get_statistics_factor(player, season)
    )
    player.price = final_price
    player.save()
    return int(final_price)


def update_match_player_ratings(match):
    try:
        home_team_tactics = TeamTactics.objects.get(team=match.home_team)
        away_team_tactics = TeamTactics.objects.get(team=match.away_team)

        home_players = home_team_tactics.starting_players.all()
        away_players = away_team_tactics.starting_players.all()

    except TeamTactics.DoesNotExist:
        print("Missing tactics for one or both teams")
        return

    all_players = list(home_players) + list(away_players)

    for player in all_players:
        update_player_rating(player, match)


def update_player_rating(player, match):
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match)
    weights = {
        'Assists': 1.0, 'CleanSheets': 1.5, 'Conceded': -1.0, 'Dribbles': 0.5,
        'Fouls': -0.2, 'Goals': 2.0, 'Matches': 0.1, 'Passes': 0.3,
        'RedCards': -1.0, 'Saves': 1.0, 'Shoots': 0.3,
        'ShootsOnTarget': 0.5, 'Tackles': 0.3, 'YellowCards': -0.5,
    }

    base_rating = 7.0
    total_weighted_score = sum(
        sum(stat.statistics.get(key, 0) * weights.get(key, 0) for key in stat.statistics)
        for stat in stats
    )
    stats_count = stats.count()

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
    current_season = get_current_season()
    player.is_free_agent = True

    Transfer.objects.create(
        season=current_season,
        selling_team=user_team,
        player=player,
        amount=0,
    )

    player.save()


def promoting_youth_players():
    Player.objects.filter(is_youth=True, age__gte=18).update(is_youth=False)


def all_players_age_up():
    Player.objects.update(age=F('age') + 1)


def update_season_statistics_for_match(match):
    # Retrieve all players for the home and away teams using the TeamPlayer model
    home_team_players = match.home_team.team_players.values_list('player', flat=True)
    away_team_players = match.away_team.team_players.values_list('player', flat=True)

    all_players = Player.objects.filter(id__in=home_team_players.union(away_team_players))

    # Iterate through all players
    for player in all_players:
        # Get PlayerMatchStatistics for the player in the match
        match_stats = PlayerMatchStatistic.objects.filter(player=player, match=match)
        for match_stat in match_stats:
            # Ensure the statistics from PlayerMatchStatistic is added to PlayerSeasonStatistic
            for stat_name, value in match_stat.statistics.items():
                statistic, _ = Statistic.objects.get_or_create(name=stat_name)
                # Get or create the PlayerSeasonStatistic for the player, season, and statistic
                season_stat, created = PlayerSeasonStatistic.objects.get_or_create(
                    player=player,
                    season=match.season,
                    statistic=statistic,
                    defaults={'value': 0}
                )
                # Update the season statistic value
                season_stat.value += value
                season_stat.save()