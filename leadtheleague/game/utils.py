from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from fixtures.utils import generate_fixtures
from game.models import Season, Settings
from leagues.models import League
from match.utils.generate_match_stats_utils import generate_matches_for_season
from players.models import Player, Statistic, PlayerSeasonStatistic
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
            season = Season(year=year, season_number=season_number, start_date=start_date, match_time=match_time)
            season.save()

            leagues = League.objects.all()
            for league in leagues:
                generate_fixtures(start_date, league, season, match_time)

            generate_matches_for_season(season)
        except IntegrityError as e:
            print("Foreign key error in Match creation:", e)
            raise
        return season


def generate_player_season_stats(player, new_season, team):
    statistics = Statistic.objects.all()
    with transaction.atomic():
        for stat in statistics:
            # Проверка дали статистиката вече съществува за играча в този сезон
            if not PlayerSeasonStatistic.objects.filter(player=player, statistic=stat, season=new_season).exists():
                # Създаване на запис със стойност по подразбиране 0
                PlayerSeasonStatistic.objects.create(
                    player=player,
                    statistic=stat,
                    season=new_season,
                    value=0
                )


def create_team_season_stats(new_season):
    with transaction.atomic():
        teams = Team.objects.all()
        for team in teams:
            if not TeamSeasonStats.objects.filter(team=team, season=new_season).exists():
                league = team.league

                TeamSeasonStats.objects.create(
                    team=team,
                    season=new_season,
                    league=league
                )

            players = Player.objects.filter(team_players__team=team)
            for player in players:
                generate_player_season_stats(player, new_season, team)


def get_setting_value(key):
    try:
        return Settings.objects.get(key=key).value
    except Settings.DoesNotExist:
        raise ValueError(f"Setting with key '{key}' does not exist!")


def delete_user(team):
    # deactivate user
    # team -> com
    pass
