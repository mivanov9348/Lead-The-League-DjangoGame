from players.models import Player
from players.utils.get_player_stats_utils import get_player_match_stats
from teams.models import TeamTactics


def get_starting_lineup(team):
    try:
        team_tactics = TeamTactics.objects.select_related('team').get(team=team)
        starting_players = team_tactics.starting_players.all().order_by('position_id')
        return starting_players
    except TeamTactics.DoesNotExist:
        return Player.objects.none()


def get_lineup_data(players, match):
    lineup_data = []
    for player in players:
        stats = get_player_match_stats(player, match)
        lineup_data.append({
            'id': player.id,
            'name': player.name,
            'goals': stats.get('goals', 0),
            'assists': stats.get('assists', 0),
            'minutesPlayed': stats.get('minutesPlayed', 0),

        })
    return lineup_data
