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


def rotate_teams(teams):
    teams[1:] = teams[-1:] + teams[1:-1]


def print_match_schedule(match_schedule):
    for match_date in match_schedule:
        print(f"Match Date: {match_date.date}, Match Time: {match_date.match_time}")


def create_fixtures(fixture_round, league_season, match_date, fixture_number):
    fixtures = []
    for home_team, away_team in fixture_round:
        fixtures.append(
            LeagueFixture(
                home_team_id=home_team,
                away_team_id=away_team,
                round_number=fixture_number,
                date=match_date.date,
                league_season=league_season,
                fixture_number=fixture_number,
                match_time=league_season.season.match_time,
            )
        )
    return fixtures


def get_team_fixtures_for_current_season(team):
    active_season = Season.objects.filter(is_active=True).first()
    if not active_season:
        return []

    league_fixtures = LeagueFixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(league_season__season=active_season)
    ).select_related('league_season__league', 'league_season__season').order_by('date', 'match_time')

    cup_fixtures = CupFixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(season_cup__season=active_season)
    ).select_related('season_cup', 'season_cup__cup').order_by('date', 'match_time')

    return chain(league_fixtures, cup_fixtures)


def get_fixtures_by_round(round_number):
    # Fetch all fixtures for the specified round
    league_fixtures = (
        LeagueFixture.objects.filter(round_number=round_number)
        .select_related('league_season__league', 'league_season__season', 'home_team', 'away_team')
        .prefetch_related(
            Prefetch('home_team', queryset=Team.objects.only('id', 'name', 'logo')),
            Prefetch('away_team', queryset=Team.objects.only('id', 'name', 'logo'))
        )
        .order_by('league_season__league__id', 'match_time')
    )

    # Group fixtures by league season
    fixtures_by_league_season = defaultdict(list)
    for fixture in league_fixtures:
        league_name = fixture.league_season.league.name
        season_year = fixture.league_season.season.year
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


def transfer_match_to_fixture(match):
    try:
        if match.fixture_content_type and match.fixture_object_id:
            fixture_model = match.fixture_content_type.model_class()
            fixture = fixture_model.objects.get(pk=match.fixture_object_id)

            fixture.home_goals = match.home_goals
            fixture.away_goals = match.away_goals

            if match.home_goals > match.away_goals:
                fixture.winner = match.home_team
            elif match.home_goals < match.away_goals:
                fixture.winner = match.away_team
            else:
                fixture.winner = None  # Равенство

            fixture.is_finished = match.is_played

            fixture.save()

            print(f"Fixture updated: {fixture}")
        else:
            print("No fixture linked to the match.")

    except Exception as e:
        print(f"Error while transferring match data to fixture: {e}")
