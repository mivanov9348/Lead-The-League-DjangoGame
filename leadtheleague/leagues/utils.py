import random

from django.db import transaction

from fixtures.models import LeagueFixture
from game.models import MatchSchedule
from teams.models import Team
from .models import League, LeagueSeason, LeagueTeams


def get_all_leagues():
    return League.objects.all()

def get_all_season_leagues(season):
    return LeagueSeason.objects.filter(season=season)


def get_selected_league(league_id):
    league = League.objects.filter(id=league_id).first()
    return league


def get_standings_for_league(league):
    league_season = LeagueSeason.objects.filter(
        league=league
    ).order_by('-season__year').first()

    if not league_season:
        return []

    return LeagueTeams.objects.filter(
        league_season=league_season
    ).select_related('team').order_by(
        '-points', '-goaldifference', '-goalscored', 'goalconceded'
    )


def get_teams_by_league(league_id):
    return Team.objects.filter(league_id=league_id) if league_id else Team.objects.none()

def check_and_mark_league_seasons_completed():
    with transaction.atomic():
        active_league_seasons = LeagueSeason.objects.filter(is_completed=False)

        for league_season in active_league_seasons:
            if not league_season.league.league_fixtures.filter(
                season=league_season.season, is_finished=False
            ).exists():
                league_season.is_completed = True
                league_season.save()

def populate_league_teams_from_json(league_season, json_data):
    league_name = league_season.league.name
    if league_name not in json_data:
        return f"No data for {league_name} in the JSON file."

    teams = json_data[league_name]
    for team_data in teams:
        team, _ = Team.objects.get_or_create(
            name=team_data["name"],
            defaults={
                "abbreviation": team_data["name"][:3].upper(),
                "reputation": team_data["reputation"],
                "nationality": league_season.league.nationality,
            },
        )

        LeagueTeams.objects.get_or_create(
            league_season=league_season,
            team=team,
            defaults={
                "matches": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goalscored": 0,
                "goalconceded": 0,
                "goaldifference": 0,
                "points": 0,
            },
        )
    return f"Teams populated for {league_name}."

def simulate_day_league_fixtures(match_day):
    with transaction.atomic():
        active_seasons = LeagueSeason.objects.filter(season__match_schedule__date=match_day)

        for league_season in active_seasons:
            league = league_season.league

            fixtures = LeagueFixture.objects.filter(
                league=league, date=match_day, is_finished=False
            )

            if not fixtures.exists():
                continue

            for fixture in fixtures:
                home_goals = random.randint(0, 7)
                away_goals = random.randint(0, 7)

                fixture.home_goals = home_goals
                fixture.away_goals = away_goals
                fixture.is_finished = True

                if home_goals > away_goals:
                    fixture.winner = fixture.home_team
                elif away_goals > home_goals:
                    fixture.winner = fixture.away_team

                fixture.save()

            update_league_standings(league_season, fixtures)

        check_and_mark_league_seasons_completed()

def update_league_standings(league_season, fixtures):
    for fixture in fixtures:
        home_team_record = LeagueTeams.objects.get(
            league_season=league_season, team=fixture.home_team
        )
        away_team_record = LeagueTeams.objects.get(
            league_season=league_season, team=fixture.away_team
        )

        # Актуализация на изиграни мачове
        home_team_record.matches += 1
        away_team_record.matches += 1

        # Резултати и точки
        home_team_record.goalscored += fixture.home_goals
        home_team_record.goalconceded += fixture.away_goals
        away_team_record.goalscored += fixture.away_goals
        away_team_record.goalconceded += fixture.home_goals

        if fixture.home_goals > fixture.away_goals:
            home_team_record.wins += 1
            away_team_record.losses += 1
            home_team_record.points += 3
        elif fixture.away_goals > fixture.home_goals:
            away_team_record.wins += 1
            home_team_record.losses += 1
            away_team_record.points += 3
        else:
            home_team_record.draws += 1
            away_team_record.draws += 1
            home_team_record.points += 1
            away_team_record.points += 1

        home_team_record.goaldifference = (
            home_team_record.goalscored - home_team_record.goalconceded
        )
        away_team_record.goaldifference = (
            away_team_record.goalscored - away_team_record.goalconceded
        )

        home_team_record.save()
        away_team_record.save()