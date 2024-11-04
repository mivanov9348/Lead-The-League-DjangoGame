import random
from fixtures.utils import update_fixtures
from game.utils import update_team_season_stats
from leagues.models import League
from match.utils import update_matches
from players.models import PlayerSeasonStats, Player
from players.utils import generate_team_players, get_player_data, auto_select_starting_lineup, update_tactics
from teams.models import AdjectiveTeamNames, NounTeamNames
from .models import Team, Division
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def generate_random_team_name():
    adjectives = list(AdjectiveTeamNames.objects.values_list('word', flat=True))
    nouns = list(NounTeamNames.objects.values_list('word', flat=True))
    return f'{random.choice(adjectives)} {random.choice(nouns)}' if random.choice([True, False]) else random.choice(nouns)

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
                name = generate_random_team_name()
                color = random.choice(colors)
                team = Team.objects.create(
                    name=name,
                    abbr=name[:3].upper(),
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
                # Transfer players from the dummy team to the new team
                dummy_team_players = Player.objects.filter(team=dummy_team)

                for player in dummy_team_players:
                    player_season_stats = PlayerSeasonStats.objects.filter(player=player, season__isnull=False).first()
                    if player_season_stats:
                        player.team = new_team
                        player.save()

                        # Create or update PlayerSeasonStats for the new team
                        PlayerSeasonStats.objects.update_or_create(
                            player=player,
                            season=player_season_stats.season,
                            defaults={
                                'stats': player_season_stats.stats,  # Link the stats directly
                                'matches_played': player_season_stats.matches_played,
                                # Add other relevant fields from player_season_stats if necessary
                            }
                        )

                update_team_season_stats(dummy_team, new_team)  # Update the stats for the new team
                update_fixtures(dummy_team, new_team)  # Update fixtures for the new team
                update_matches(dummy_team, new_team)
                update_tactics(dummy_team, new_team)

                dummy_team.delete()

                new_team.division = division  # Set the division for the new team
                new_team.save()

                return True
    return False

def get_team_players_season_data(team):
    players = Player.objects.filter(team=team)
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
