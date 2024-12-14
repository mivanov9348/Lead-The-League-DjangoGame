from django.db import IntegrityError
from fixtures.models import LeagueFixture, CupFixture
from teams.models import Team
from datetime import timedelta
import random

def generate_fixtures(start_date, league, season, match_time):
    last_fixture = LeagueFixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    teams = list(Team.objects.filter(league=league))
    random.shuffle(teams)

    if len(teams) % 2 != 0:
        teams.append(None)

    total_rounds = len(teams) - 1
    half_size = len(teams) // 2
    current_date = start_date
    round_number = 1

    schedule = []

    for r in range(total_rounds):
        round_pairs = []
        for i in range(half_size):
            home_team = teams[i]
            away_team = teams[-(i + 1)]

            if home_team is not None and away_team is not None:
                if r % 2 == 0:
                    round_pairs.append((home_team, away_team))
                else:
                    round_pairs.append((away_team, home_team))

        schedule.append(round_pairs)
        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    return_legs = []
    for fixture_round in schedule:
        return_legs.append([(away, home) for home, away in fixture_round])

    full_schedule = schedule + return_legs

    for fixture_round in full_schedule:
        for home_team, away_team in fixture_round:
            LeagueFixture.objects.create(
                home_team=home_team,
                away_team=away_team,
                round_number=round_number,
                date=current_date,
                league=league,
                fixture_number=fixture_number,
                season=season,
                match_time=match_time
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

    return round_number

def create_cup_fixture(season_cup, fixture_number, home_team, away_team, round_stage, round_number=1, match_time="18:00", date=None):
    try:
        fixture = CupFixture.objects.create(
            fixture_number=fixture_number,
            home_team=home_team,
            away_team=away_team,
            round_number=round_number,
            date=date,
            match_time=match_time,
            season=season_cup.season,
            season_cup=season_cup,
            round_stage=round_stage,
        )
        print(f"Created: {home_team.name} vs {away_team.name} за '{round_stage}'.")
        return fixture
    except IntegrityError as e:
        print(f"Error when trying to create CupFixture: {e}")
        return None
