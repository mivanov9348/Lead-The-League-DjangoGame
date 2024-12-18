from collections import defaultdict
from django.db.models import Prefetch, Max
from fixtures.models import LeagueFixture
import random
from game.models import MatchSchedule
from teams.models import Team


def generate_league_fixtures(league_season):
    league_teams = list(league_season.teams.select_related('team'))
    teams = [lt.team for lt in league_teams]

    if len(teams) % 2 != 0:
        teams.append(None)  # Добавяме празен отбор, ако броят е нечетен

    random.shuffle(teams)

    total_rounds = len(teams) - 1
    half_size = len(teams) // 2

    # Генерираме мачовете за първия етап
    schedule = []
    for _ in range(total_rounds):
        round_pairs = []
        for i in range(half_size):
            home_team = teams[i]
            away_team = teams[-(i + 1)]
            if home_team and away_team:
                round_pairs.append((home_team, away_team))

        schedule.append(round_pairs)
        teams = [teams[0]] + teams[-1:] + teams[1:-1]  # Завъртане на отборите

    # Генерираме мачовете за втория етап (реванши)
    return_legs = [[(away, home) for home, away in round_pairs] for round_pairs in schedule]
    full_schedule = schedule + return_legs

    # Намираме съществуващите фикстури за лигата
    last_fixture_number = (
        LeagueFixture.objects.aggregate(Max('fixture_number')).get('fixture_number__max') or 0
    )
    fixture_number = last_fixture_number + 1

    # Намираме наличния график за лигата в текущия сезон
    league_match_schedule = MatchSchedule.objects.filter(
        season=league_season.season,
        event_type='league',
    ).order_by('date')

    if not league_match_schedule.exists():
        raise ValueError("No match schedule available for league fixtures in the current season.")

    # Уверяваме се, че имаме достатъчно дати в графика
    if len(league_match_schedule) < len(full_schedule):
        raise ValueError("Not enough dates in the league match schedule to generate fixtures.")

    # Създаваме фикстурите
    bulk_create_list = []
    round_number = 1

    for match_date, fixture_round in zip(league_match_schedule, full_schedule):
        for home_team, away_team in fixture_round:
            # Добавяме фикстура към списъка за създаване
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



def get_fixtures_by_round(round_number=None):
    if round_number is None:
        round_number = 1

    league_fixtures = (
        LeagueFixture.objects.filter(round_number=round_number)
        .select_related('league', 'season', 'home_team', 'away_team')
        .prefetch_related(
            Prefetch('home_team', queryset=Team.objects.only('id', 'name', 'logo')),
            Prefetch('away_team', queryset=Team.objects.only('id', 'name', 'logo'))
        )
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
