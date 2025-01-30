from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When, Value, BooleanField

from django.shortcuts import get_object_or_404
from fixtures.models import LeagueFixture, EuropeanCupFixture, CupFixture
from game.models import Season
from leagues.models import League, LeagueTeams
from match.models import Match
from teams.models import Team, TeamFinance
from vault.models import TeamAllStats


def get_all_teams():
    return Team.objects.all()

def get_sorted_teams():
    league_teams = (
        LeagueTeams.objects
        .select_related('team', 'league_season__league')
        .filter(team__isnull=False)
        .order_by(
            'league_season__league__name',  # Подреждане първо по лига
            Case(
                When(team__is_active=False, then=Value(1)),  # is_active=False -> отива в края
                When(team__is_active=True, then=Value(0)),   # is_active=True -> първо
                output_field=BooleanField()
            ),
            'team__name'  # Допълнителна подредба по име
        )
    )

    unique_teams = []
    seen_teams = set()

    for league_team in league_teams:
        if league_team.team.id not in seen_teams:
            unique_teams.append(league_team.team)
            seen_teams.add(league_team.team.id)

    return unique_teams


def get_team_balance(user_team):
    team_finance = TeamFinance.objects.filter(team=user_team).first()
    return team_finance.balance if team_finance else 0


from itertools import chain
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def get_poster_schedule(league, user_team, season):
    fixtures_by_type = get_fixtures_by_team_and_type(user_team)

    # Combine all fixtures into one iterable
    all_fixtures = chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    )

    matches = []
    for fixture in all_fixtures:
        # Determine location and opponent
        location = 'H' if fixture.home_team == user_team else 'A'
        opponent = fixture.away_team if location == 'H' else fixture.home_team
        result = f"{fixture.home_goals} - {fixture.away_goals}" if fixture.is_finished else "TBD"

        # Find or create the match object
        content_type = ContentType.objects.get_for_model(fixture)
        match = Match.objects.filter(
            fixture_content_type=content_type,
            fixture_object_id=fixture.id,
            season=season
        ).first()

        # If the match does not exist, create a new one
        if not match:
            match_data = {
                'home_team': fixture.home_team,
                'away_team': fixture.away_team,
                'match_date': fixture.date,
                'match_time': fixture.match_time,
                'home_goals': fixture.home_goals,
                'away_goals': fixture.away_goals,
                'is_played': fixture.is_finished,
                'stadium': getattr(fixture.home_team, 'stadium', None),
                'season': season,
                'fixture_content_type': content_type,
                'fixture_object_id': fixture.id,
            }
            match = Match(**match_data)

        if isinstance(fixture, LeagueFixture):
            competition = f"League"
        elif isinstance(fixture, CupFixture):
            competition = f"Cup"
        elif isinstance(fixture, EuropeanCupFixture):
            competition = f"Europe"
        else:
            competition = "Unknown"

        # Append enriched match data to the result list
        matches.append({
            'match': match,
            'date': match.match_date,
            'opponent': opponent,
            'location': location,
            'result': result,
            'competition': competition,
        })

    # Sort matches by date
    matches_sorted = sorted(matches, key=lambda x: x['date'])

    return matches_sorted


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
    all_time_stats = TeamAllStats.objects.filter(team=team).first()

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
        'all_time_stats': {
            'matches': all_time_stats.matches if all_time_stats else 0,
            'wins': all_time_stats.wins if all_time_stats else 0,
            'draws': all_time_stats.draws if all_time_stats else 0,
            'loses': all_time_stats.loses if all_time_stats else 0,
            'goal_scored': all_time_stats.goal_scored if all_time_stats else 0,
            'goal_conceded': all_time_stats.goal_conceded if all_time_stats else 0,
            'points': all_time_stats.points if all_time_stats else 0,
            'league_titles': all_time_stats.league_titles if all_time_stats else 0,
            'cup_titles': all_time_stats.cup_titles if all_time_stats else 0,
            'euro_cup_titles': all_time_stats.euro_cup_titles if all_time_stats else 0,
        } if all_time_stats else None,
    }
    return team_data