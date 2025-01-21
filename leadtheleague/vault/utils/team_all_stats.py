from django.db import transaction

from players.models import PlayerMatchStatistic
from vault.models import TeamAllStats, PlayerAllStats


def get_all_team_all_stats():
    return TeamAllStats.objects.all()

def get_team_all_stats_by_team(team):
    try:
        return TeamAllStats.objects.get(team=team)
    except TeamAllStats.DoesNotExist:
        return None


def update_team_all_time_stats_after_match(match):
    home_team_stats, _ = TeamAllStats.objects.get_or_create(team=match.home_team)
    away_team_stats, _ = TeamAllStats.objects.get_or_create(team=match.away_team)

    home_team_stats.matches += 1
    away_team_stats.matches += 1

    home_team_stats.goal_scored += match.home_goals
    home_team_stats.goal_conceded += match.away_goals
    away_team_stats.goal_scored += match.away_goals
    away_team_stats.goal_conceded += match.home_goals

    if match.home_goals > match.away_goals:
        home_team_stats.wins += 1
        away_team_stats.loses += 1
        home_team_stats.points += 3
    elif match.home_goals < match.away_goals:
        away_team_stats.wins += 1
        home_team_stats.loses += 1
        away_team_stats.points += 3
    else:
        home_team_stats.draws += 1
        away_team_stats.draws += 1
        home_team_stats.points += 1
        away_team_stats.points += 1

    home_team_stats.save()
    away_team_stats.save()


def add_league_title(team):
    with transaction.atomic():
        team_stats, created = TeamAllStats.objects.get_or_create(team=team)
        team_stats.league_titles += 1
        team_stats.save()

def add_cup_title(team):
    with transaction.atomic():
        team_stats, created = TeamAllStats.objects.get_or_create(team=team)
        team_stats.cup_titles += 1
        team_stats.save()

def add_euro_cup_title(team):
    with transaction.atomic():
        team_stats, created = TeamAllStats.objects.get_or_create(team=team)
        team_stats.euro_cup_titles += 1
        team_stats.save()