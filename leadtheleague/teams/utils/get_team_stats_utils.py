from itertools import chain
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from fixtures.models import LeagueFixture, EuropeanCupFixture, CupFixture
from game.models import Season
from teams.models import Team, TeamFinance

def get_all_teams():
    return Team.objects.all()

def get_team_balance(user_team):
    team_finance = TeamFinance.objects.filter(team=user_team).first()
    return team_finance.balance if team_finance else 0

def get_poster_schedule(league, user_team):
    fixtures_by_type = get_fixtures_by_team_and_type(user_team)

    # Combine all fixtures into one iterable
    all_fixtures = chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    )

    schedule_data = []
    for fixture in all_fixtures:
        location = 'H' if fixture.home_team == user_team else 'A'
        opponent = fixture.away_team if location == 'H' else fixture.home_team
        result = f"{fixture.home_goals} - {fixture.away_goals}" if fixture.is_finished else None

        if isinstance(fixture, LeagueFixture):
            competition_type = "League"
        elif isinstance(fixture, CupFixture):
            competition_type = f"Cup - {fixture.round_stage}"
        elif isinstance(fixture, EuropeanCupFixture):
            competition_type = f"Euro - {fixture.round_stage}"
        else:
            competition_type = "Unknown"

        schedule_data.append({
            'date': fixture.date,
            'opponent': opponent,
            'location': location,
            'result': result or "TBD",
            'competition': competition_type,
        })

    schedule_data_sorted = sorted(schedule_data, key=lambda x: x['date'])

    return schedule_data_sorted

def get_fixtures_by_team_and_type(team):
    active_season = Season.objects.filter(is_active=True).first()
    if not active_season:
        return {
            "league": [],
            "cup": [],
            "euro": [],
        }

    league_fixtures = LeagueFixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(league_season__season=active_season)
    ).select_related('league_season', 'league_season__league').order_by('date', 'match_time')

    cup_fixtures = CupFixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(season_cup__season=active_season)
    ).select_related('season_cup', 'season_cup__cup').order_by('date', 'match_time')

    euro_fixtures = EuropeanCupFixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(european_cup_season__season=active_season)
    ).select_related('european_cup_season', 'group', 'knockout_stage').order_by('date', 'match_time')

    return {
        "league": league_fixtures,
        "cup": cup_fixtures,
        "euro": euro_fixtures,
    }


def get_team_data(team_id):
    team = get_object_or_404(Team, id=team_id, is_active=True)

    finances = TeamFinance.objects.filter(team=team).first()

    team_data = {
        'id': team.id,
        'name': team.name,
        'abbreviation': team.abbreviation,
        'reputation': team.reputation,
        'logo_url': team.logo.url if team.logo else None,
        'nationality': team.nationality.name if team.nationality else 'Unknown',
        'nationality_abbr': team.nationality.abbreviation if team.nationality else 'Unknown',
        'finances': {
            'balance': finances.balance if finances else 0.00,
            'total_income': finances.total_income if finances else 0.00,
            'total_expenses': finances.total_expenses if finances else 0.00,
        },
    }
    return team_data



