from players.models import Player
from players.utils.get_player_stats_utils import get_player_stats
from teams.models import TeamTactics


def get_starting_lineup(team):
    try:
        tactics = TeamTactics.objects.get(team=team)
        starting_players = [player.id for player in tactics.starting_players.all()]
        return starting_players
    except TeamTactics.DoesNotExist:
        print(f"No tactics found for team {team.name}. Returning an empty list.")
        return []

def get_lineup_data(players, match):
    lineup_data = []
    for player in players:
        stats = get_player_stats(player, match)
        lineup_data.append({
            'id': player.id,
            'name': player.name,
            'goals': stats.get('goals', 0),
            'assists': stats.get('assists', 0),
            'minutesPlayed': stats.get('minutesPlayed', 0),

        })
    return lineup_data

