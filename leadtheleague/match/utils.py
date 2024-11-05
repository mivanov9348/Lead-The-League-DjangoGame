from fixtures.models import Fixture
from game.models import Season
from players.models import Player, PlayerMatchStatistic, Statistic
from .models import Match
from datetime import datetime
import random

def generate_matches_for_season(season):
    fixtures = Fixture.objects.filter(season=season)

    for fixture in fixtures:
        Match.objects.create(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            division=fixture.division,
            date=datetime.combine(fixture.date, fixture.match_time),
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        )

def update_matches(dummy_team, new_team):
    home_matches = Match.objects.filter(home_team=dummy_team)
    away_matches = Match.objects.filter(away_team=dummy_team)

    for match in home_matches:
        match.home_team = new_team
        match.save()

    for match in away_matches:
        match.away_team = new_team
        match.save()

def get_current_minute(request):
    current_minute = request.session.get('current_minute', 0)
    increment = random.randint(1, 5)
    current_minute += increment

    if current_minute > 90:
        current_minute = 90

    return current_minute

def generate_player_match_stats():
    current_season = Season.objects.filter(is_ended=False).first()  # Вземете първия несвършен сезон
    if not current_season:
        print("Няма активен сезон.")
        return

    matches = Match.objects.filter(season=current_season)
    players = Player.objects.all()

    for match in matches:
        for player in players:
            if player.team in [match.home_team, match.away_team]:
                for statistic in Statistic.objects.all():
                    PlayerMatchStatistic.objects.create(
                        player=player,
                        match=match,
                        statistic=statistic,
                        value=0
                    )

    print(f"PlayerMatchStats успешно създадени за всички играчи в {len(matches)} мача.")  # Печат за потвърждение
