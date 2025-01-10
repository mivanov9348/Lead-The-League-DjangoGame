from players.models import Player, PositionAttribute, PlayerAttribute
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

def select_best_starting_players_by_position(grouped_players, num_required, position):
    ranked_players = sorted(
        grouped_players,
        key=lambda player: calculate_player_rating_by_position_and_attributes(player, position),
        reverse=True
    )
    return ranked_players[:num_required]

def calculate_player_rating_by_position_and_attributes(player, position):
    position_attributes = PositionAttribute.objects.filter(position=position)
    player_attributes = PlayerAttribute.objects.filter(player=player)

    rating = 0

    for pos_attr in position_attributes:
        player_attr = player_attributes.filter(attribute=pos_attr.attribute).first()
        if player_attr:
            rating += pos_attr.importance * player_attr.value

    return rating
