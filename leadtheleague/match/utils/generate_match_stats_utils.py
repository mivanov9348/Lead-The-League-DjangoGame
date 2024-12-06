from django.utils import timezone
from fixtures.models import Fixture
from game.models import Season
from match.models import Match
from players.models import Player, Statistic, PlayerMatchStatistic, PlayerSeasonStatistic

def generate_matches_for_season(season):
    fixtures = Fixture.objects.filter(season=season)
    matches_to_create = []

    for fixture in fixtures:
        matches_to_create.append(Match(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            league =fixture.league,
            match_date=fixture.date,
            match_time=fixture.match_time,
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        ))

    Match.objects.bulk_create(matches_to_create)

def generate_players_match_stats_for_today():
    current_season = Season.objects.filter(is_ended=False).first()
    if not current_season:
        return

    today = timezone.now().date()
    matches = Match.objects.filter(season=current_season, match_date=today)
    players = Player.objects.prefetch_related('team_players').all()

    for match in matches:
        for player in players:
            teams = player.team_players.values_list('team', flat=True)
            if match.home_team_id in teams or match.away_team_id in teams:
                generate_player_match_stats(player, match)

def generate_player_match_stats(player, match):
    player_match_statistics = [
        PlayerMatchStatistic(
            player=player,
            match=match,
            statistic=statistic,
            value=0
        ) for statistic in Statistic.objects.all()
    ]
    PlayerMatchStatistic.objects.bulk_create(player_match_statistics)

def generate_player_season_stats(player, season, team):
    for statistic in Statistic.objects.all():
        if not PlayerSeasonStatistic.objects.filter(player=player, season=season, statistic=statistic).exists():
            PlayerSeasonStatistic.objects.create(
                player=player,
                season=season,
                statistic=statistic,
                value=0,
            )