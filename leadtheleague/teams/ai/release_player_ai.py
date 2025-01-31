import random
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from messaging.utils.category_messages_utils import create_release_player_message
from players.models import Position
from players.utils.update_player_stats_utils import release_player_from_team
from staff.utils.agent_utils import hire_agent_to_player
from teams.models import Team, TeamPlayer

teams = Team.objects.filter(user__isnull=True).select_related('teamfinance')

def ai_calculate_position_strength(team, position_abbr):
    position = get_object_or_404(Position, abbreviation=position_abbr)
    players = TeamPlayer.objects.filter(team=team, player__position=position)

    if not players.exists():
        return 0

    return players.aggregate(Avg('player__potential_rating'))['player__potential_rating__avg']

def can_release_player(team):
    required_positions = {
        "Goalkeeper": 1,
        "Defender": 5,
        "Midfielder": 5,
        "Attacker": 3,
    }

    team_players = TeamPlayer.objects.filter(team=team).select_related("player")
    position_count = {pos: 0 for pos in required_positions.keys()}

    for team_player in team_players:
        if not team_player.player.is_youth:
            position_name = team_player.player.position.name
            if position_name in position_count:
                position_count[position_name] += 1

    print(f"Checking release conditions for {team.name}")
    for position_name, required_count in required_positions.items():
        current_count = position_count.get(position_name, 0)
        print(f"Position: {position_name}, Current: {current_count}, Required: {required_count}")
        if current_count <= required_count:
            print(f"Cannot release player, insufficient players in position: {position_name}")
            return False

    return True

def ai_decide_release_players():
    print("Starting AI process to release players...")
    for team in teams:
        print(f"Processing team: {team.name}")
        team_avg_rating = TeamPlayer.objects.filter(team=team).aggregate(Avg('player__potential_rating'))
        team_avg_rating = team_avg_rating['player__potential_rating__avg'] or 0

        players = TeamPlayer.objects.filter(team=team).select_related('player')

        for team_player in players:
            player = team_player.player
            player_avg_rating = ai_calculate_position_strength(team, player.position.abbreviation)

            if player_avg_rating < team_avg_rating and player.potential_rating < team_avg_rating:
                if can_release_player(team):
                    print(f"Releasing player: {player.first_name} {player.last_name} from {team.name}")
                    release_player_from_team(team, player)
                    hire_agent_to_player(None, player)
                    create_release_player_message(player, team)
                else:
                    print(f"Cannot release {player.first_name} {player.last_name}, insufficient squad depth.")

    print("AI player release process completed.")
