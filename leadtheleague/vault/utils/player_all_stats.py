from django.db import transaction

from players.models import PlayerMatchStatistic
from vault.models import PlayerAllStats


def get_all_player_all_stats():
    return PlayerAllStats.objects.all()


def get_player_all_stats_by_player(player):
    try:
        return PlayerAllStats.objects.get(player=player)
    except PlayerAllStats.DoesNotExist:
        return None


def update_player_stats_for_match(match):
    try:
        print(f"Updating player statistics for match: {match}")

        # Prefetch related data to minimize database queries
        player_match_stats = PlayerMatchStatistic.objects.filter(match=match).select_related('player')

        players_to_update = []
        created_players = set()

        with transaction.atomic():
            for player_stat in player_match_stats:
                print(f"Processing statistics for player: {player_stat.player.name}")

                # Get or create the all-time stats for the player
                player_stats, created = PlayerAllStats.objects.select_for_update().get_or_create(
                    player=player_stat.player)

                if created:
                    print(f"Created new all-time stats record for player: {player_stat.player.name}")
                    created_players.add(player_stat.player)

                # Extract statistics from the match
                match_statistics = player_stat.statistics
                matches_played = match_statistics.get('Matches', 0)
                goals_scored = match_statistics.get('Goals', 0)
                print(
                    f"Match statistics for {player_stat.player.name}: Matches: {matches_played}, Goals: {goals_scored}")

                # Update the all-time stats
                player_stats.matches += matches_played
                player_stats.goals += goals_scored

                players_to_update.append(player_stats)

            # Bulk update the player stats
            PlayerAllStats.objects.bulk_update(players_to_update, ['matches', 'goals'])

            for player_stat in players_to_update:
                print(
                    f"Updated all-time stats for player: {player_stat.player.name} -> Matches: {player_stat.matches}, Goals: {player_stat.goals}"
                )

        # Update points after all stats are updated
        update_all_players_points()

    except Exception as e:
        print(f"Error updating player statistics for match {match}: {e}")


def update_all_players_points():
    for player_stats in PlayerAllStats.objects.all():
        player_stats.save()
