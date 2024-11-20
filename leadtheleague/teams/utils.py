import random
from collections import defaultdict

from django.db import transaction
from fixtures.utils import update_fixtures
from game.utils import update_team_season_stats
from leagues.models import League, Division
from match.utils import update_matches
from players.models import Player, PlayerSeasonStatistic, Statistic
from players.utils import generate_team_players, get_player_data, auto_select_starting_lineup, update_tactics
from teams.models import TeamSeasonStats, DummyTeamNames
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
        if not Team.objects.filter(name=team_name).exists() and not Team.objects.filter(abbreviation=team_abbr).exists():
            return team_name, team_abbr


def fill_dummy_teams():
    Team.objects.filter(is_dummy=True).delete()
    colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Black', 'White']
    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')

        for division in divisions:
            existing_team_count = Team.objects.filter(division=division).count()
            teams_needed = division.teams_count - existing_team_count

            for _ in range(teams_needed):
                team_name, team_abbr = generate_random_team_name()
                color = random.choice(colors)
                team = Team.objects.create(
                    name=team_name,
                    abbreviation=team_abbr,
                    color=color,
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
def get_team_players_season_data(team):
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

    with transaction.atomic():
        home_stats.matches += 1
        away_stats.matches += 1

    if home_goals > away_goals:
        home_stats.wins += 1
        home_stats.points += 3
        away_stats.losses += 1

    elif home_goals < away_goals:
        away_stats.wins += 1
        away_stats.points += 3
        home_stats.losses += 1

    else:
        home_stats.draws += 1
        away_stats.draws += 1
        home_stats.points += 1
        away_stats.points += 1

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