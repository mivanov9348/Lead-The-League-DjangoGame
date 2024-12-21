from itertools import chain

from django.shortcuts import get_object_or_404

from fixtures.utils import get_fixtures_by_team_and_type, format_fixtures
from players.models import Player
from players.utils.get_player_stats_utils import get_player_data
from teams.models import Team, TeamFinance


def get_all_teams():
    return Team.objects.all()


def get_team_players_season_stats(team):
    players = Player.objects.filter(team_players__team=team)
    standings_data = []

    for player in players:
        player_data = get_player_data(player)
        standings_data.append(player_data)

    return standings_data


def get_team_balance(user):
    if user.is_authenticated and hasattr(user, 'teams'):
        team_finance = TeamFinance.objects.filter(team=user.team).first()
        return team_finance.balance if team_finance else 0
    return


def get_poster_schedule(league, user_team):
    fixtures_by_type = get_fixtures_by_team_and_type(user_team)

    all_fixtures = chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    )

    formatted_fixtures = format_fixtures(all_fixtures, user_team)

    schedule_data = []
    for fixture in formatted_fixtures:
        print(f'fixture: {fixture}')
        location = 'H' if fixture["home_away"] == "Home" else 'A'
        opponent = fixture["opponent"]
        if fixture['is_finished']:
            result = f'{fixture['home_goals']}' "-" f'{fixture['away_goals']}'
        else:
            result = "TBD"

        schedule_data.append({
            'date': fixture["date"],
            'opponent': opponent,
            'location': location,
            'result': result
        })

    return schedule_data


def get_team_schedule(team):
    fixtures_by_type = get_fixtures_by_team_and_type(team)
    all_fixtures = chain(
        fixtures_by_type["league"], fixtures_by_type["cup"], fixtures_by_type["euro"]
    )
    return format_fixtures(all_fixtures, team)


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
