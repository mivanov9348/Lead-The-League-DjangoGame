import random
from collections import defaultdict
from django.db import transaction
from fixtures.utils import update_fixtures
from game.models import Settings
from game.utils import update_team_season_stats
from leagues.models import League, Division
from match.utils.generate_match_stats_utils import update_matches
from players.models import Player, PlayerSeasonStatistic, Statistic
from players.utils.generate_player_utils import generate_team_players
from players.utils.get_player_stats_utils import get_player_data
from teams.models import TeamSeasonStats, DummyTeamNames, TeamTactics, Tactics
from .models import Team
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def generate_random_team_name():
    all_team_info = list(DummyTeamNames.objects.values_list('name', 'abbreviation'))

    while True:
        # Генерираме случайно име и абревиатура
        team_name, team_abbr = random.choice(all_team_info)
        # Проверяваме дали отбор с това име и абревиатура вече съществува
        if not Team.objects.filter(name=team_name).exists() and not Team.objects.filter(
                abbreviation=team_abbr).exists():
            return team_name, team_abbr


def fill_dummy_teams():
    Team.objects.filter(is_dummy=True).delete()
    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')

        for division in divisions:
            existing_team_count = Team.objects.filter(division=division).count()
            teams_needed = division.teams_count - existing_team_count

            for _ in range(teams_needed):
                team_name, team_abbr = generate_random_team_name()
                team = Team.objects.create(
                    name=team_name,
                    abbreviation=team_abbr,
                    user=None,
                    is_dummy=True,
                    division=division
                )
                generate_team_players(team)
                auto_select_starting_lineup(team)


def replace_dummy_team(new_team):
    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')
        for division in divisions:
            dummy_team = Team.objects.filter(division=division, is_dummy=True).first()
            if dummy_team:
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
                update_fixtures(dummy_team, new_team)  # Актуализиране на фикстурите за новия отбор
                update_matches(dummy_team, new_team)
                update_tactics(dummy_team, new_team)

                dummy_team.delete()

                new_team.division = division  # Задаване на дивизията за новия отбор
                new_team.save()

                return True
    return False

def get_all_teams():
    return Team.objects.all()


def get_team_players_season_stats(team):
    # Филтриране на играчите чрез релацията team_players
    players = Player.objects.filter(team_players__team=team)
    standings_data = []

    for player in players:
        player_data = get_player_data(player)
        standings_data.append(player_data)

    return standings_data


def create_team_performance_chart(season_stats, team_name):
    stats_data = {
        "Year": [],
        "Season": [],
        "Matches": [],
        "Wins": [],
        "Draws": [],
        "Losses": [],
        "Goals Scored": [],
        "Goals Against": [],
        "Goal Difference": [],
        "Points": []
    }

    for stat in season_stats:
        stats_data["Year"].append(stat.season.year)
        stats_data["Season"].append(stat.season.season_number)
        stats_data["Matches"].append(stat.matches)
        stats_data["Wins"].append(stat.wins)
        stats_data["Draws"].append(stat.draws)
        stats_data["Losses"].append(stat.losses)
        stats_data["Goals Scored"].append(stat.goalscored)
        stats_data["Goals Against"].append(stat.goalconceded)
        stats_data["Goal Difference"].append(stat.goaldifference)
        stats_data["Points"].append(stat.points)

    df = pd.DataFrame(stats_data)

    plt.figure(figsize=(10, 5))
    plt.plot(df["Season"], df["Wins"], label="Wins", marker='o')
    plt.plot(df["Season"], df["Draws"], label="Draws", marker='o')
    plt.plot(df["Season"], df["Losses"], label="Losses", marker='o')
    plt.title(f"{team_name} Performance Over Seasons")
    plt.xlabel("Season")
    plt.xticks(rotation=45)
    plt.ylabel("Number of Matches")
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')

    return img


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
        home_stats.points +=  win_points
        away_stats.losses += 1

    elif home_goals < away_goals:
        away_stats.wins += 1
        away_stats.points +=  win_points
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

def create_position_template(selected_tactic, starting_players):
    if not selected_tactic:
        return []

    position_template = []

    tactic_positions = {
        'GK': selected_tactic.num_goalkeepers,
        'DF': selected_tactic.num_defenders,
        'MF': selected_tactic.num_midfielders,
        'ATT': selected_tactic.num_attackers
    }

    for abbreviation, count in tactic_positions.items():
        for _ in range(count):
            position_template.append({"abbreviation": abbreviation, "player": None})

    position_map = defaultdict(list)
    for player in starting_players:
        position_map[player.position.abbreviation].append(player)

    used_players = set()
    slot_counts = defaultdict(int)

    for slot in position_template:
        available_players = [
            player for player in position_map[slot['abbreviation']]
            if player not in used_players and slot_counts[slot['abbreviation']] < tactic_positions[slot['abbreviation']]
        ]

        if available_players:
            selected_player = available_players[0]
            slot["player"] = selected_player
            used_players.add(selected_player)
            slot_counts[slot['abbreviation']] += 1

    return position_template


# lineup utils (team)
def auto_select_starting_lineup(team):
    """
    Автоматично избира стартов състав за даден отбор на базата на наличните тактики.
    """
    team_tactics, created = TeamTactics.objects.get_or_create(team=team)
    if team_tactics.starting_players.count() >= 11:
        return

    tactic = Tactics.objects.order_by('?').first()
    if not tactic:
        raise ValueError("Няма налични тактики в базата данни.")

    required_positions = {
        'GK': tactic.num_goalkeepers,
        'DF': tactic.num_defenders,
        'MF': tactic.num_midfielders,
        'ATT': tactic.num_attackers,
    }

    selected_players = {key: [] for key in required_positions.keys()}
    players = Player.objects.filter(team_players__team=team)

    for player in players:
        pos_abbr = player.position.abbreviation
        if pos_abbr in required_positions and len(selected_players[pos_abbr]) < required_positions[pos_abbr]:
            selected_players[pos_abbr].append(player)

    team_tactics.starting_players.set(
        [player for sublist in selected_players.values() for player in sublist]
    )
    team_tactics.tactic = tactic
    team_tactics.save()

    return selected_players


# lineup utils (team)
def update_tactics(dummy_team, new_team):
    """
    Актуализира тактиките на новият отбор на базата на dummy_team.
    """
    dummy_team_tactics = TeamTactics.objects.filter(team=dummy_team).first()
    if dummy_team_tactics:
        TeamTactics.objects.update_or_create(
            team=new_team,
            defaults={'tactic': dummy_team_tactics.tactic}
        )
