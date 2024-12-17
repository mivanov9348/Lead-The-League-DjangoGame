from django.db import IntegrityError
from fixtures.models import LeagueFixture, CupFixture
from datetime import timedelta
import random

def generate_league_fixtures(league_season, start_date, match_time="18:00"):
    league_teams = list(league_season.teams.all())
    teams = [lt.team for lt in league_teams]

    random.shuffle(teams)

    if len(teams) % 2 != 0:
        teams.append(None)

    total_rounds = len(teams) - 1
    half_size = len(teams) // 2
    current_date = start_date
    round_number = 1

    schedule = []
    for _ in range(total_rounds):
        round_pairs = []
        for i in range(half_size):
            home_team = teams[i]
            away_team = teams[-(i + 1)]

            if home_team and away_team:  # Игнориране на почивния отбор
                round_pairs.append((home_team, away_team))

        schedule.append(round_pairs)
        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    return_legs = [[(away, home) for home, away in round_pairs] for round_pairs in schedule]
    full_schedule = schedule + return_legs

    last_fixture = LeagueFixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    for fixture_round in full_schedule:
        for home_team, away_team in fixture_round:
            LeagueFixture.objects.create(
                home_team=home_team,
                away_team=away_team,
                round_number=round_number,
                date=current_date,
                league=league_season.league,
                season=league_season.season,
                fixture_number=fixture_number,
                match_time=match_time,
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

    return f"Fixtures generated for LeagueSeason: {league_season}."

def create_cup_fixture(season_cup, fixture_number, home_team, away_team, round_stage, round_number=1,
                       match_time="18:00", date=None):
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

from collections import defaultdict

def get_fixtures_by_round(round_number=None):
    if round_number is None:
        round_number = 1  # По подразбиране първи кръг

    league_fixtures = (
        LeagueFixture.objects.filter(round_number=round_number)
        .select_related('league', 'season', 'home_team', 'away_team')
        .order_by('season__league__id', 'match_time')
    )

    fixtures_by_league_season = defaultdict(list)
    for fixture in league_fixtures:
        league_season_key = f"{fixture.season.league.name} ({fixture.season.season.name})"
        fixtures_by_league_season[league_season_key].append({
            "time": fixture.match_time.strftime('%H:%M'),
            "home_team": {
                "name": fixture.home_team.name,
                "logo": fixture.home_team.logo.url if fixture.home_team.logo else None,
            },
            "away_team": {
                "name": fixture.away_team.name,
                "logo": fixture.away_team.logo.url if fixture.away_team.logo else None,
            },
            "league_name": fixture.league.name,
        })

    return fixtures_by_league_season
