from django.db.models import Q

from fixtures.models import CupFixture, LeagueFixture
from players.models import Player
from players.utils.get_player_stats_utils import get_player_data
from teams.models import Team, TeamFinance

def get_all_teams():
    return Team.objects.all()

def get_team_players_season_stats(team):
    # Филтриране на играчите чрез релацията team_players
    players = Player.objects.filter(team_players__team=team)
    standings_data = []

    for player in players:
        player_data = get_player_data(player)
        standings_data.append(player_data)

    return standings_data


def get_team_balance(user):
    if user.is_authenticated and hasattr(user, 'team'):
        team_finance = TeamFinance.objects.filter(team=user.team).first()
        return team_finance.balance if team_finance else 0
    return

def get_team_schedule(league, user_team):
    if not league or not user_team:
        return None

    league_schedule = LeagueFixture.objects.filter(
        Q(league=league) & (Q(home_team=user_team) | Q(away_team=user_team))
    ).order_by('date', 'match_time')

    cup_schedule = CupFixture.objects.filter(
        (Q(home_team=user_team) | Q(away_team=user_team))
    ).order_by('date', 'match_time')

    combined_schedule = sorted(
        list(league_schedule) + list(cup_schedule),
        key=lambda fixture: (fixture.date, fixture.match_time)
    )

    return combined_schedule

def get_poster_schedule(league, user_team):
    team_schedule = get_team_schedule(league, user_team)
    if not team_schedule:
        return []

    schedule_data = []
    for fixture in team_schedule:
        if fixture.home_team == user_team:
            opponent = fixture.away_team
            location = 'H'  # Home
        else:
            opponent = fixture.home_team
            location = 'A'  # Away

        schedule_data.append({
            'date': fixture.date,
            'opponent': opponent,
            'location': location
        })

    return schedule_data
