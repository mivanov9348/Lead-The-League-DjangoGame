import random
from collections import defaultdict
from django.db.models import Count

from match.utils.match.lineup import select_best_starting_players_by_position
from players.models import Player, Position
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


def validate_lineup(players, selected_tactic):
    grouped_players = {
        'goalkeeper': 0,
        'defender': 0,
        'midfielder': 0,
        'attacker': 0,
    }

    for player in players:
        if player.position.abbreviation == 'GK':
            grouped_players['goalkeeper'] += 1
        elif player.position.abbreviation == 'DF':
            grouped_players['defender'] += 1
        elif player.position.abbreviation == 'MF':
            grouped_players['midfielder'] += 1
        elif player.position.abbreviation == 'ATT':
            grouped_players['attacker'] += 1

    errors = []

    if grouped_players['goalkeeper'] != selected_tactic.num_goalkeepers:
        errors.append("Incorrect number of goalkeepers selected.")
    if grouped_players['defender'] != selected_tactic.num_defenders:
        errors.append("Incorrect number of defenders selected.")
    if grouped_players['midfielder'] != selected_tactic.num_midfielders:
        errors.append("Incorrect number of midfielders selected.")
    if grouped_players['attacker'] != selected_tactic.num_attackers:
        errors.append("Incorrect number of attackers selected.")

    return errors


def ensure_team_tactics(match):
    teams = [match.home_team, match.away_team]


    for team in teams:
        TeamTactics.objects.filter(team=team).delete()
        auto_select_starting_lineup(team)

def auto_select_starting_lineup(team):
    try:
        print(f"Processing team: {team}")

        tactics = Tactics.objects.all()
        print(f"Available tactics: {[tactic.name for tactic in tactics]}")

        if not tactics.exists():
            raise ValueError("No tactics available in the database.")

        all_players = Player.objects.filter(
            team_players__team=team,
            is_youth=False,
            is_free_agent=False
        )

        print(f"Total players in team {team.name}: {all_players.count()}")

        grouped_players = {
            'goalkeeper': [],
            'defender': [],
            'midfielder': [],
            'attacker': [],
        }

        for player in all_players:
            if player.position.abbreviation == 'GK':
                grouped_players['goalkeeper'].append(player)
            elif player.position.abbreviation == 'DF':
                grouped_players['defender'].append(player)
            elif player.position.abbreviation == 'MF':
                grouped_players['midfielder'].append(player)
            elif player.position.abbreviation == 'ATT':
                grouped_players['attacker'].append(player)

        print(f"Grouped players: { {k: len(v) for k, v in grouped_players.items()} }")

        valid_tactics = [
            tactic for tactic in tactics if
            len(grouped_players['goalkeeper']) >= tactic.num_goalkeepers and
            len(grouped_players['defender']) >= tactic.num_defenders and
            len(grouped_players['midfielder']) >= tactic.num_midfielders and
            len(grouped_players['attacker']) >= tactic.num_attackers
        ]

        print(f"Valid tactics for team {team.name}: {[tactic.name for tactic in valid_tactics]}")

        if not valid_tactics:
            raise ValueError("No valid tactics available based on the current squad.")

        selected_tactic = random.choice(valid_tactics)
        print(f"Selected tactic: {selected_tactic.name}")

        selected_players = (
            select_best_starting_players_by_position(grouped_players['goalkeeper'], selected_tactic.num_goalkeepers, Position.objects.get(abbreviation='GK')) +
            select_best_starting_players_by_position(grouped_players['defender'], selected_tactic.num_defenders, Position.objects.get(abbreviation='DF')) +
            select_best_starting_players_by_position(grouped_players['midfielder'], selected_tactic.num_midfielders, Position.objects.get(abbreviation='MF')) +
            select_best_starting_players_by_position(grouped_players['attacker'], selected_tactic.num_attackers, Position.objects.get(abbreviation='ATT'))
        )

        print(f"Selected players for team {team.name}: {[player.name for player in selected_players]}")

        errors = validate_lineup(selected_players, selected_tactic)
        if errors:
            print(f"Validation errors for team {team.name}: {errors}")
            raise ValueError("; ".join(errors))

        team_tactics, _ = TeamTactics.objects.get_or_create(team=team)
        team_tactics.tactic = selected_tactic
        team_tactics.starting_players.clear()

        for player in selected_players:
            team_tactics.starting_players.add(player)

        team_tactics.save()
        print(f"Lineup successfully saved for team {team.name}.")

    except Exception as e:
        print(f"Error occurred for team {team.name}: {str(e)}")
        raise ValueError(f"Failed to auto-select lineup: {str(e)}")


def validate_team_minimums(team):
    team_players = team.team_players.select_related('player__position').values(
        'player__position__abbreviation'
    ).annotate(count=Count('id'))

    grouped_players = {
        'GK': 0,
        'DF': 0,
        'MF': 0,
        'ATT': 0
    }

    for player in team_players:
        pos = player['player__position__abbreviation']
        count = player['count']

        if pos == 'GK':
            grouped_players['GK'] += count
        elif pos == 'DF':
            grouped_players['DF'] += count
        elif pos == 'MF':
            grouped_players['MF'] += count
        elif pos == 'ATT':
            grouped_players['ATT'] += count

    total_players = sum(grouped_players.values())

    if total_players < 11:
        return False

    if grouped_players['GK'] < 1:
        return False

    if grouped_players['DF'] < 3:
        return False

    if grouped_players['MF'] < 3:
        return False

    if grouped_players['ATT'] < 1:
        return False

    return True
