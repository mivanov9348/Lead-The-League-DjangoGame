import json
import os

from core.models import Nationality
from leadtheleague import settings
from teams.models import TeamSeasonStats, Team
from .models import League, LeagueSeason, LeagueTeams


def get_all_leagues():
    return League.objects.all()


def get_selected_league(league_id):
    league = League.objects.filter(id=league_id).first()
    return league


def get_standings_for_league(league):
    return TeamSeasonStats.objects.filter(
        league=league
    ).select_related('team').order_by('-points', '-goalscored', 'goalconceded')


def get_teams_by_league(league_id):
    return Team.objects.filter(league_id=league_id) if league_id else Team.objects.none()


def setup_leagues_and_teams_from_json(season):
    json_path = os.path.join(settings.BASE_DIR, "static/data/leagues_and_teams.json")

    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("JSON file not found!")
        return
    except json.JSONDecodeError:
        print("Error when read JSON!")
        return

    for league_name, teams in data.items():
        try:
            league_season = LeagueSeason.objects.get(league__name=league_name, season=season)
        except LeagueSeason.DoesNotExist:
            print(f"Няма LeagueSeason за '{league_name}' и сезон {season}.")
            continue

        nationality, _ = Nationality.objects.get_or_create(name=league_season.league.nationality)

        add_teams_to_league_season(league_season, teams, nationality)

    print("Setup complete.")

def add_teams_to_league_season(league_season, teams, nationality):
    for team_data in teams:
        team, _ = Team.objects.get_or_create(
            name=team_data['name'],
            defaults={
                'abbreviation': team_data['name'][:3].upper(),
                'reputation': team_data['reputation'],
                'nationality': nationality
            }
        )

        league_team, created = LeagueTeams.objects.get_or_create(
            league_season=league_season,
            team=team,
            defaults={
                'matches': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goalscored': 0,
                'goalconceded': 0,
                'goaldifference': 0,
                'points': 0
            }
        )

        if created:
            print(f"Added {team.name} to {league_season.league.name} - season {league_season.season}.")
        else:
            print(f"{team.name} is already in {league_season.league.name} - season {league_season.season}.")
