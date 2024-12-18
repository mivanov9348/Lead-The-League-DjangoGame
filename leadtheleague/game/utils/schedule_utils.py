import datetime
import random
from datetime import timedelta
from itertools import cycle
from math import ceil, log2
from europeancups.models import EuropeanCupSeason
from game.models import MatchSchedule


def get_max_league_rounds(season):
    league_seasons = season.league_seasons.select_related('league')
    max_teams = max((ls.league.teams_count for ls in league_seasons), default=0)
    return (max_teams - 1) * 2 if max_teams >= 2 else 0


def get_max_cup_rounds(season):
    season_cups = season.season_cups.prefetch_related('participating_teams')
    max_teams = max((sc.participating_teams.count() for sc in season_cups), default=0)
    return ceil(log2(max_teams)) if max_teams >= 2 else 0

def get_max_euro_rounds(season):
    euro_seasons = EuropeanCupSeason.objects.filter(season=season).only(
        'teams_per_group', 'total_teams_qualify_from_group', 'groups_count'
    )
    total_rounds = 0

    for euro_season in euro_seasons:
        group_matches = euro_season.teams_per_group * (euro_season.teams_per_group - 1)
        group_rounds = group_matches // 2
        knockout_rounds = ceil(log2(euro_season.total_teams_qualify_from_group * euro_season.groups_count))
        total_rounds = max(total_rounds, group_rounds + knockout_rounds)

    return total_rounds


def generate_season_schedule(season):
    max_league_rounds = get_max_league_rounds(season)
    max_cup_rounds = get_max_cup_rounds(season)
    print(f'max_cup_rounds: {max_cup_rounds}')

    max_euro_rounds = get_max_euro_rounds(season)

    total_matches = (
        ['league'] * max_league_rounds +
        ['cup'] * max_cup_rounds +
        ['euro'] * max_euro_rounds
    )

    total_days = len(total_matches)
    print(f'total_days: {total_days}')

    current_date = season.start_date

    schedule = [None] * total_days

    schedule[-2] = 'cup'
    schedule[-1] = 'euro'

    remaining_matches = (
        ['league'] * max_league_rounds +
        ['cup'] * (max_cup_rounds - 1) +
        ['euro'] * (max_euro_rounds - 1)
    )

    random.shuffle(remaining_matches)

    for i in range(total_days - 2):
        if schedule[i] is None:
            for match in remaining_matches:
                if match == 'cup' and (i > 0 and schedule[i - 1] == 'cup'):
                    continue
                if match == 'euro' and (i > 0 and schedule[i - 1] == 'euro'):
                    continue
                schedule[i] = match
                remaining_matches.remove(match)
                break

    for i in range(total_days):
        if schedule[i] is None:
            schedule[i] = 'league'

    match_schedules = []
    for i, event_type in enumerate(schedule):
        match_date = current_date + timedelta(days=i)
        match_schedules.append(MatchSchedule(date=match_date, season=season, event_type=event_type))

    MatchSchedule.objects.bulk_create(match_schedules)

    season.end_date = current_date + timedelta(days=total_days - 1)
    season.save()