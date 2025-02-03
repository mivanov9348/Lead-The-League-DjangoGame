from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404

from messaging.utils.category_messages_utils import create_release_player_message
from players.models import Position
from players.utils.update_player_stats_utils import release_player_from_team
from staff.utils.agent_utils import hire_agent_to_player
from teams.models import TeamPlayer


class ReleaseAI:
    @staticmethod
    def manage_player_releases(team):
        print(f"Processing player release for: {team.name}")

        team_avg_rating = TeamPlayer.objects.filter(team=team).aggregate(Avg('player__potential_rating'))
        team_avg_rating = team_avg_rating['player__potential_rating__avg'] or 0

        players = TeamPlayer.objects.filter(team=team).select_related('player')

        for team_player in players:
            player = team_player.player
            player_avg_rating = ReleaseAI.calculate_position_strength(team, player.position.abbreviation)

            if player_avg_rating < team_avg_rating and player.potential_rating < team_avg_rating:
                if ReleaseAI.can_release_player(team):
                    ReleaseAI.release_player(team, player)
                else:
                    print(f"Cannot release {player.first_name} {player.last_name}, insufficient squad depth.")

    @staticmethod
    def calculate_position_strength(team, position_abbr):
        position = get_object_or_404(Position, abbreviation=position_abbr)
        players = TeamPlayer.objects.filter(team=team, player__position=position)

        if not players.exists():
            return 0

        return players.aggregate(Avg('player__potential_rating'))['player__potential_rating__avg']

    @staticmethod
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

        for position_name, required_count in required_positions.items():
            current_count = position_count.get(position_name, 0)
            if current_count <= required_count:
                return False

        return True

    @staticmethod
    def release_player(team, player):
        try:
            with transaction.atomic():
                print(f"Releasing player: {player.first_name} {player.last_name} from {team.name}")
                release_player_from_team(team, player)
                hire_agent_to_player(None, player)
                create_release_player_message(player, team)
        except Exception as e:
            print(f"Error releasing player {player.first_name} {player.last_name}: {e}")