from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import DivisionTeam, Division
from players.models import Player, PlayerAttribute, PlayerSeasonStats
from teams.models import Team, TeamSeasonStats
from datetime import date


def get_team_home_data(user):
    team = Team.objects.get(user=user)
    players = Player.objects.filter(team=team)

    player_data = []
    for player in players:
        attributes = PlayerAttribute.objects.filter(player=player).select_related('attribute')
        player_data.append({
            'player': player,
            'attributes': attributes
        })

    division_team = DivisionTeam.objects.get(team=team)
    division = division_team.division
    standings = DivisionTeam.objects.filter(division=division)

    user_team_index = list(standings).index(division_team)

    if user_team_index <= 1:
        centered_standings = standings[:5]
    elif user_team_index >= len(standings) - 2:
        centered_standings = standings[-5:]
    else:
        centered_standings = standings[user_team_index - 2:user_team_index + 3]

    return {
        'team': team,
        'manager_name': team.user.username,
        'player_count': players.count(),
        'player_data': player_data,
        'standings': centered_standings,
    }


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
        return season  # Return the existing season
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
                # Извличане на свързаните DivisionTeam записи
                division_team = DivisionTeam.objects.filter(team=team).first()

                if division_team:
                    league = division_team.division.league  # Вземете лигата от дивизията
                    division = division_team.division  # Вземете дивизията от DivisionTeam

                    TeamSeasonStats.objects.create(
                        team=team,
                        season=new_season,
                        league=league,
                        division=division
                    )

            players = Player.objects.filter(team=team)
            for player in players:
                if not PlayerSeasonStats.objects.filter(player=player, season=new_season).exists():
                    PlayerSeasonStats.objects.create(
                        player=player,
                        season=new_season,
                        team=team
                    )
