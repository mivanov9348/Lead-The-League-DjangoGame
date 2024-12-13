from django.db import transaction
from django.utils import timezone
from fixtures.models import LeagueFixture, CupFixture
from game.models import Season
from match.models import Match
from players.models import Player, PlayerMatchStatistic

def generate_matches_for_season(season):
    matches_to_create = []

    # Обработка на LeagueFixture
    league_fixtures = LeagueFixture.objects.filter(season=season)
    for fixture in league_fixtures:
        matches_to_create.append(Match(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            league=fixture.league,
            match_date=fixture.date,
            match_time=fixture.match_time,
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        ))

    # Обработка на CupFixture
    cup_fixtures = CupFixture.objects.filter(season=season)
    for fixture in cup_fixtures:
        matches_to_create.append(Match(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            league=None,  # Cup fixtures may not have an associated league
            match_date=fixture.date,
            match_time=fixture.match_time,
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        ))

    # Създаване на всички мачове в една транзакция
    with transaction.atomic():
        Match.objects.bulk_create(matches_to_create)

def generate_player_day_match_stats_by_player(player, today=None):
    today = today or timezone.now().date()
    current_season = Season.objects.filter(is_ended=False).first()
    if not current_season:
        return

    matches = Match.objects.filter(season=current_season, match_date=today)

    with transaction.atomic():
        for match in matches:
            teams = player.team_players.values_list('team', flat=True)
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
                        }
                    )


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
                teams = player.team_players.values_list('team', flat=True)
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
                            }
                        )
