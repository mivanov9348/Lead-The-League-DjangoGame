from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import Division
from match.utils import generate_matches_for_season, generate_player_match_stats
from players.models import Player, PlayerSeasonStatistic, Statistic
from teams.models import Team, TeamSeasonStats


def get_current_season(year=None):
    if year is not None:
        current_season = Season.objects.filter(year=year).order_by('-season_number').first()
    else:
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
        try:
            # Create and save the Season instance first
            season = Season(year=year, season_number=season_number, start_date=start_date, match_time=match_time)
            season.save()

            # Only after the season is fully saved, generate fixtures and matches
            divisions = Division.objects.all()
            for division in divisions:
                generate_fixtures(start_date, division, season, match_time)  # Pass the saved instance

            # Generate matches and player stats only after the season exists
            generate_matches_for_season(season)
        except IntegrityError as e:
            print("Foreign key error in Match creation:", e)
            raise
        return season

def create_team_season_stats(new_season):
    with transaction.atomic():
        teams = Team.objects.all()
        for team in teams:
            if not TeamSeasonStats.objects.filter(team=team, season=new_season).exists():
                division = team.division

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
        for statistic in Statistic.objects.all():
            if not PlayerSeasonStatistic.objects.filter(player=player, season=new_season, statistic=statistic).exists():
                PlayerSeasonStatistic.objects.create(
                    player=player,
                    season=new_season,
                    statistic=statistic,
                    value=0,
                )

def update_team_season_stats(dummy_team, new_team):
    team_season_stats = TeamSeasonStats.objects.filter(team=dummy_team)
    for stats in team_season_stats:
        stats.team = new_team
        stats.save()
