from fixtures.models import Fixture
from .models import Match
from datetime import datetime

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
            is_played=fixture.is_finished
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