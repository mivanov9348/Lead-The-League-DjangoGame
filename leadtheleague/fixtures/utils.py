from collections import defaultdict
from datetime import date
from itertools import chain
from django.db.models import Prefetch, Max, Q
from fixtures.models import LeagueFixture, CupFixture, EuropeanCupFixture
import random
from game.models import MatchSchedule, Season
from leagues.models import LeagueSeason
from teams.models import Team
from django.db import transaction


def get_fixtures_by_date(target_date=None):
    if target_date is None:
        target_date = date.today()  # Default to today's date if no date is provided

    if not isinstance(target_date, date):
        raise ValueError(f"Invalid target_date: {target_date}. Expected datetime.date object.")

    league_fixtures = LeagueFixture.objects.filter(date=target_date)
    cup_fixtures = CupFixture.objects.filter(date=target_date)
    european_cup_fixtures = EuropeanCupFixture.objects.filter(date=target_date)

    all_fixtures = list(league_fixtures) + list(cup_fixtures) + list(european_cup_fixtures)
    return all_fixtures

def generate_all_league_fixtures(season):
    print(f"Starting fixture generation for season: {season}")  # Дебъг: вход

    league_seasons = LeagueSeason.objects.filter(season=season)
    print(f"Found league seasons: {list(league_seasons)}")  # Дебъг: извеждане на намерените сезони

    if not league_seasons.exists():
        print("No LeagueSeason instances found.")  # Дебъг: ако няма сезони
        return f"No LeagueSeason instances found for the season: {season}."

    errors = []
    with transaction.atomic():
        for league_season in league_seasons:
            try:
                print(f"Processing LeagueSeason: {league_season}")  # Дебъг: текущо състояние
                generate_league_fixtures_for_season(league_season)
            except Exception as e:
                error_message = f"Error generating fixtures for {league_season}: {str(e)}"
                print(error_message)  # Дебъг: пълна информация за грешката
                errors.append(error_message)

    if errors:
        print(f"Errors occurred: {errors}")
        return f"Some errors occurred:\n" + "\n".join(errors)

    print("Successfully completed fixture generation for all league seasons.")
    return f"Fixtures successfully generated for all LeagueSeasons in season: {season}."


def generate_league_fixtures_for_season(league_season):
    league_teams = list(league_season.teams.select_related('team'))
    teams = [lt.team for lt in league_teams]

    if len(teams) % 2 != 0:
        teams.append(None)

    random.shuffle(teams)

    total_rounds = len(teams) - 1
    half_size = len(teams) // 2

    schedule = []
    for _ in range(total_rounds):
        round_pairs = []
        for i in range(half_size):
            home_team = teams[i]
            away_team = teams[-(i + 1)]
            if home_team and away_team:
                round_pairs.append((home_team, away_team))

        schedule.append(round_pairs)
        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    return_legs = [[(away, home) for home, away in round_pairs] for round_pairs in schedule]
    full_schedule = schedule + return_legs

    last_fixture_number = (
            LeagueFixture.objects.aggregate(Max('fixture_number')).get('fixture_number__max') or 0
    )
    fixture_number = last_fixture_number + 1

    league_match_schedule = MatchSchedule.objects.filter(
        season=league_season.season,
        event_type='league',
    ).order_by('date')

    if not league_match_schedule.exists():
        raise ValueError("No match schedule available for league fixtures in the current season.")

    if len(league_match_schedule) < len(full_schedule):
        raise ValueError("Not enough dates in the league match schedule to generate fixtures.")

    bulk_create_list = []
    round_number = 1

    for match_date, fixture_round in zip(league_match_schedule, full_schedule):
        for home_team, away_team in fixture_round:
            bulk_create_list.append(
                LeagueFixture(
                    home_team=home_team,
                    away_team=away_team,
                    round_number=round_number,
                    date=match_date.date,
                    league_season=league_season,
                    fixture_number=fixture_number,
                    match_time=match_date.season.match_time,  # Използваме времето от сезона
                )
            )
            fixture_number += 1

        match_date.is_league_day_assigned = True
        match_date.save()

        round_number += 1

    LeagueFixture.objects.bulk_create(bulk_create_list)
