from collections import defaultdict
from itertools import chain
from django.db.models import Prefetch, Max, Q
from fixtures.models import LeagueFixture, CupFixture, EuropeanCupFixture
import random
from game.models import MatchSchedule
from teams.models import Team


def generate_league_fixtures(league_season):
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

    # Намираме съществуващите фикстури за лигата
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
                    league=league_season.league,
                    season=league_season.season,
                    fixture_number=fixture_number,
                    match_time=match_date.season.match_time,  # Използваме времето от сезона
                )
            )
            fixture_number += 1

        match_date.is_league_day_assigned = True
        match_date.save()

        round_number += 1

    LeagueFixture.objects.bulk_create(bulk_create_list)

    return f"Fixtures successfully generated for LeagueSeason: {league_season}."


def get_poster_schedule(league, user_team):
    # Retrieve fixtures by type (league, cup, euro) for the user's teams
    fixtures_by_type = get_fixtures_by_team_and_type(user_team)

    # Combine all fixtures into one iterable
    all_fixtures = chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    )

    # Prepare the schedule data in the required format
    schedule_data = []
    for fixture in all_fixtures:
        print(fixture)
        location = 'H' if fixture.home_team == user_team else 'A'
        opponent = fixture.away_team if location == 'H' else fixture.home_team

        schedule_data.append({
            'date': fixture.date,
            'opponent': opponent,
            'location': location
        })

    return schedule_data


def get_team_schedule(team):
    fixtures_by_type = get_fixtures_by_team_and_type(team)
    all_fixtures = chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    )
    return list(all_fixtures)


def get_fixtures_by_round(round_number):
    # Fetch all fixtures for the specified round
    league_fixtures = (
        LeagueFixture.objects.filter(round_number=round_number)
        .select_related('league', 'season', 'home_team', 'away_team')
        .prefetch_related(
            Prefetch('home_team', queryset=Team.objects.only('id', 'name', 'logo')),
            Prefetch('away_team', queryset=Team.objects.only('id', 'name', 'logo'))
        )
        .order_by('league__id', 'match_time')
    )

    # Group fixtures by league and season
    fixtures_by_league_season = defaultdict(list)
    for fixture in league_fixtures:
        league_name = fixture.league.name
        season_year = fixture.season.year
        league_season_key = f"{league_name} ({season_year})"

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
            "home_goals": fixture.home_goals if fixture.is_finished else None,
            "away_goals": fixture.away_goals if fixture.is_finished else None,
        })

    return fixtures_by_league_season


def get_fixtures_by_team_and_type(team):
    league_fixtures = LeagueFixture.objects.filter(
        Q(home_team=team) | Q(away_team=team)
    ).select_related('league', 'season').order_by('date', 'match_time')

    cup_fixtures = CupFixture.objects.filter(
        Q(home_team=team) | Q(away_team=team)
    ).select_related('season_cup', 'season_cup__cup').order_by('date', 'match_time')

    euro_fixtures = EuropeanCupFixture.objects.filter(
        Q(home_team=team) | Q(away_team=team)
    ).select_related('european_cup_season', 'group', 'knockout_stage').order_by('date', 'match_time')

    return {
        "league": league_fixtures,
        "cup": cup_fixtures,
        "euro": euro_fixtures,
    }


def format_fixtures(fixtures, team):
    formatted_fixtures = []

    for fixture in fixtures:
        fixture_info = {
            "date": fixture.date,
            "round": getattr(fixture, 'round_number', getattr(fixture, 'round_stage', '')),
            "home_away": "Home" if fixture.home_team == team else "Away",
            'home_goals': fixture.home_goals,
            'away_goals': fixture.away_goals,
            "opponent": fixture.away_team if fixture.home_team == team else fixture.home_team,
            "time": fixture.match_time.strftime("%H:%M") if fixture.match_time else "No Time",
            "is_finished": fixture.is_finished,
            "type": (
                "League" if isinstance(fixture, LeagueFixture)
                else "Cup" if isinstance(fixture, CupFixture)
                else "European"
            ),
        }
        formatted_fixtures.append(fixture_info)

    return formatted_fixtures
