from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import Division
from players.models import Player, PlayerAttribute, PlayerSeasonStats
from teams.models import Team, TeamSeasonStats
from datetime import date

def get_current_season(year):
    current_season = Season.objects.filter(year=year).order_by('-season_number').first()

    if current_season and isinstance(current_season.end_date, date):
        if current_season.end_date >= date.today():
            return current_season


def generate_season_number(year):
    seasons = get_current_season(year)
    return seasons.count() + 1


def create_new_season(year, season_number, start_date, match_time):

    try:
        season = Season.objects.get(year=year, season_number=season_number)
        return season
    except ObjectDoesNotExist:
        season = Season.objects.create(year=year, season_number=season_number, start_date=start_date,
                                       match_time=match_time)

        divisions = Division.objects.all()

        for division in divisions:
            generate_fixtures(start_date, division, season, match_time)

        return season

def create_team_season_stats(new_season):
    with transaction.atomic():
        teams = Team.objects.all()
        for team in teams:
            if not TeamSeasonStats.objects.filter(team=team, season=new_season).exists():
                division = team.division
                print(f'divisia {division}')
                league = division.league

                TeamSeasonStats.objects.create(
                    team=team,
                    season=new_season,
                    league=league,
                    division=division
                )

            # Get players for the team and create PlayerSeasonStats
            players = Player.objects.filter(team=team)
            for player in players:
                if not PlayerSeasonStats.objects.filter(player=player, season=new_season).exists():
                    PlayerSeasonStats.objects.create(
                        player=player,
                        season=new_season,
                        team=team
                    )