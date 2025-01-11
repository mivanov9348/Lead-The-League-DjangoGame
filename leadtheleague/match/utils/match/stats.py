from django.db import transaction
from django.utils import timezone
from game.models import Season
from match.models import Match
from players.models import PlayerMatchStatistic, Player
from teams.models import TeamTactics

def generate_players_match_stats(match):
    home_tactics = TeamTactics.objects.filter(team=match.home_team).first()
    away_tactics = TeamTactics.objects.filter(team=match.away_team).first()

    if not home_tactics or not away_tactics:
        raise ValueError("Team tactics not found for one of the teams.")

    starting_players = list(home_tactics.starting_players.all()) + list(away_tactics.starting_players.all())

    statistics = [
        "Assists", "CleanSheets", "Conceded", "Dribbles", "Fouls", "Goals", "Matches",
         "Passes", "RedCards", "Saves", "Shoots", "ShootsOnTarget",
        "Tackles", "YellowCards"
    ]

    with transaction.atomic():
        existing_stats = PlayerMatchStatistic.objects.filter(match=match).values_list('player_id', flat=True)

        new_stats = []
        for player in starting_players:
            if player.id not in existing_stats:
                stats_data = {stat: 0 for stat in statistics}
                new_stats.append(
                    PlayerMatchStatistic(
                        player=player,
                        match=match,
                        statistics=stats_data
                    )
                )

        PlayerMatchStatistic.objects.bulk_create(new_stats)

def generate_all_player_day_match_stats():
    today = timezone.now().date()
    current_season = Season.objects.filter(is_ended=False).first()
    if not current_season:
        return

    matches = Match.objects.filter(season=current_season, match_date=today)

    players = Player.objects.prefetch_related('team_players').filter(is_free_agent=False)

    with transaction.atomic():
        for match in matches:
            for player in players:
                teams = player.team_players.values_list('teams', flat=True)
                if match.home_team_id in teams or match.away_team_id in teams:
                    if not PlayerMatchStatistic.objects.filter(player=player, match=match).exists():
                        PlayerMatchStatistic.objects.create(
                            player=player,
                            match=match,
                            statistics={
                                "Goals": 0,
                                "Assists": 0,
                                "Passes": 0,
                                "Shoots": 0,
                                "ShootsOnTarget": 0,
                                "Tackles": 0,
                                "YellowCards": 0,
                                "RedCards": 0,
                                "Saves": 0,
                                "Matches": 0
                            }
                        )
