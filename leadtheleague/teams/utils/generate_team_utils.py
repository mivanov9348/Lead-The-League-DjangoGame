import os
import random
from django.db import transaction
from fixtures.utils import update_fixtures
from game.models import Settings
from game.utils import update_team_season_stats
from leadtheleague import settings
from leagues.models import League, Division
from match.utils.generate_match_stats_utils import update_matches
from players.models import Player, PlayerSeasonStatistic, Statistic
from players.utils.generate_player_utils import generate_team_players
from teams.models import DummyTeamNames, Team, TeamSeasonStats
from teams.utils.lineup_utils import auto_select_starting_lineup, update_tactics
from teams.utils.team_finance_utils import create_team_finance, terminate_team_finance

def generate_random_team_name():
    all_team_info = list(DummyTeamNames.objects.values_list('name', 'abbreviation'))

    while True:
        # Генерираме случайно име и абревиатура
        team_name, team_abbr = random.choice(all_team_info)
        # Проверяваме дали отбор с това име и абревиатура вече съществува
        if not Team.objects.filter(name=team_name).exists() and not Team.objects.filter(
                abbreviation=team_abbr).exists():
            return team_name, team_abbr


# generate_team_utils.py
def fill_dummy_teams():
    Team.objects.filter(is_dummy=True).delete()
    leagues = League.objects.all().order_by('level')

    logos_path = os.path.join(settings.MEDIA_ROOT, 'team_logos')
    logo_files = [f for f in os.listdir(logos_path) if os.path.isfile(os.path.join(logos_path, f))]

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')

        for division in divisions:
            existing_team_count = Team.objects.filter(division=division).count()
            teams_needed = division.teams_count - existing_team_count

            for _ in range(teams_needed):
                team_name, team_abbr = generate_random_team_name()
                random_logo = random.choice(logo_files)
                logo_path = os.path.join('team_logos', random_logo)
                team = Team.objects.create(
                    name=team_name,
                    abbreviation=team_abbr,
                    user=None,
                    is_dummy=True,
                    division=division,
                    logo=logo_path
                )
                generate_team_players(team)
                auto_select_starting_lineup(team)
                create_team_finance(team)

# generate_team_utils.py
def replace_dummy_team(new_team):
    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')
        for division in divisions:
            dummy_team = Team.objects.filter(division=division, is_dummy=True).first()
            if dummy_team:
                new_team.logo = dummy_team.logo  # Прехвърляне на логото на Dummy Team към новия отбор
                new_team.save()  # Запазваме новия отбор с новото лого
                # Прехвърляне на играчите от Dummy Team към новия отбор
                dummy_team_players = Player.objects.filter(team_players__team=dummy_team)

                for player in dummy_team_players:
                    # Извличане на сезона на играча
                    player_season_stats = PlayerSeasonStatistic.objects.filter(player=player,
                                                                               season__isnull=False).first()
                    if player_season_stats:
                        player.team_players.update(team=new_team)
                        player.save()

                        for statistic in Statistic.objects.all():

                            season_stat = PlayerSeasonStatistic.objects.filter(player=player,
                                                                               season=player_season_stats.season,
                                                                               statistic=statistic).first()

                            if season_stat:
                                # Създаване или актуализиране на PlayerSeasonStatistic за новия отбор
                                PlayerSeasonStatistic.objects.update_or_create(
                                    player=player,
                                    season=player_season_stats.season,
                                    statistic=statistic,
                                    defaults={
                                        'value': season_stat.value,  # Запазваме стойността на статистиката
                                    }
                                )

                update_team_season_stats(dummy_team, new_team)  # Актуализиране на статистиките за новия отбор
                # Префиксиране на логото и статуса на новия отбор
                new_team.logo = dummy_team.logo
                new_team.save()
                update_fixtures(dummy_team, new_team)  # Актуализиране на фикстурите за новия отбор
                update_matches(dummy_team, new_team)
                update_tactics(dummy_team, new_team)

                terminate_team_finance(dummy_team)

                dummy_team.delete()
                create_team_finance(new_team)

                new_team.division = division  # Задаване на дивизията за новия отбор
                new_team.logo = dummy_team.logo  # Прехвърляне на логото на Dummy Team към новия отбор
                new_team.save()  # Запазваме новия отбор с новото лого
                new_team.division = division  # Задаване на дивизията за новия отбор
                new_team.save()

                return True
    return False


def update_team_stats(match):
    if not match.is_played:
        print('Match is still unplayed!')
        return

    home_team = match.home_team
    away_team = match.away_team
    home_goals = match.home_goals
    away_goals = match.away_goals

    home_stats, _ = TeamSeasonStats.objects.get_or_create(
        team=home_team,
        season=match.season,
        division=match.division
    )
    away_stats, _ = TeamSeasonStats.objects.get_or_create(
        team=away_team,
        season=match.season,
        division=match.division
    )

    draw_points = Settings.objects.get(name='League_Draw_Points').value
    win_points = Settings.objects.get(name='League_Win_Points').value

    with transaction.atomic():
        home_stats.matches += 1
        away_stats.matches += 1

    if home_goals > away_goals:
        home_stats.wins += 1
        home_stats.points += win_points
        away_stats.losses += 1

    elif home_goals < away_goals:
        away_stats.wins += 1
        away_stats.points += win_points
        home_stats.losses += 1

    else:
        home_stats.draws += 1
        away_stats.draws += 1
        home_stats.points += draw_points
        away_stats.points += draw_points

    home_stats.goalscored += home_goals
    home_stats.goalconceded += away_goals
    away_stats.goalscored += away_goals
    away_stats.goalconceded += home_goals

    home_stats.goaldifference = home_stats.goalscored - home_stats.goalconceded
    away_stats.goaldifference = away_stats.goalscored - away_stats.goalconceded

    home_stats.save()
    away_stats.save()
