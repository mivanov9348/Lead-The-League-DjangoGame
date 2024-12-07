from collections import defaultdict
from players.models import Player
from teams.models import TeamTactics, Tactics


def create_position_template(selected_tactic, starting_players):
    if not selected_tactic:
        return []

    position_template = []

    tactic_positions = {
        'GK': selected_tactic.num_goalkeepers,
        'DF': selected_tactic.num_defenders,
        'MF': selected_tactic.num_midfielders,
        'ATT': selected_tactic.num_attackers
    }

    for abbreviation, count in tactic_positions.items():
        for _ in range(count):
            position_template.append({"abbreviation": abbreviation, "player": None})

    position_map = defaultdict(list)
    for player in starting_players:
        position_map[player.position.abbreviation].append(player)

    used_players = set()
    slot_counts = defaultdict(int)

    for slot in position_template:
        available_players = [
            player for player in position_map[slot['abbreviation']]
            if player not in used_players and slot_counts[slot['abbreviation']] < tactic_positions[slot['abbreviation']]
        ]

        if available_players:
            selected_player = available_players[0]
            slot["player"] = selected_player
            used_players.add(selected_player)
            slot_counts[slot['abbreviation']] += 1

    return position_template


def auto_select_starting_lineup(team):
    team_tactics, created = TeamTactics.objects.get_or_create(team=team)
    if team_tactics.starting_players.count() >= 11:
        return

    tactic = Tactics.objects.order_by('?').first()
    if not tactic:
        raise ValueError("No tactics in database.")

    required_positions = {
        'GK': tactic.num_goalkeepers,
        'DF': tactic.num_defenders,
        'MF': tactic.num_midfielders,
        'ATT': tactic.num_attackers,
    }

    selected_players = {key: [] for key in required_positions.keys()}
    players = Player.objects.filter(team_players__team=team)

    for player in players:
        pos_abbr = player.position.abbreviation
        if pos_abbr in required_positions and len(selected_players[pos_abbr]) < required_positions[pos_abbr]:
            selected_players[pos_abbr].append(player)

    team_tactics.starting_players.set(
        [player for sublist in selected_players.values() for player in sublist]
    )
    team_tactics.tactic = tactic
    team_tactics.save()

    return selected_players


def update_tactics(new_team):
    COM_teams_tactics = TeamTactics.objects.filter(is_COM=True).first()
    if COM_teams_tactics:
        TeamTactics.objects.update_or_create(
            team=new_team,
            defaults={'tactic': COM_teams_tactics.tactic}
        )
