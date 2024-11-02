from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import Division
from players.models import Player, PlayerSeasonStats, PlayerStats
from teams.models import Team, TeamSeasonStats

def get_current_season(year=None):
    if year is not None:
        # Filter by year if provided
        current_season = Season.objects.filter(year=year).order_by('-season_number').first()
    else:
        # If year is None, get the latest unended season
        current_season = Season.objects.filter(is_ended=False).order_by('-season_number').first()

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
            create_player_season_stats(players, new_season, team)


def create_player_season_stats(players, new_season, team):
    for player in players:
        # Check if the PlayerSeasonStats for the player and season already exists
        if not PlayerSeasonStats.objects.filter(player=player, season=new_season).exists():
            # Create a new PlayerStats instance
            player_stats = PlayerStats.objects.create()  # Add any defaults or initial values here if needed

            # Create PlayerSeasonStats with the new PlayerStats
            PlayerSeasonStats.objects.create(
                player=player,
                season=new_season,
                stats=player_stats,  # Link the new PlayerStats instance
                matches_played=0,  # You can initialize matches played or any other fields as needed
            )


def update_team_season_stats(dummy_team, new_team):
    team_season_stats = TeamSeasonStats.objects.filter(team=dummy_team)
    for stats in team_season_stats:
        stats.team = new_team
        stats.save()