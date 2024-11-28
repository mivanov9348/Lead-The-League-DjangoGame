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
    return 0