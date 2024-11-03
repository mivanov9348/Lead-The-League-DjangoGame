from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
import logging
from players.utils import get_player_data
from .forms import TeamCreationForm
from players.models import Player
from teams.models import Team, TeamTactics, Tactics, TeamSeasonStats
from django.contrib.auth.decorators import login_required
from .utils import replace_dummy_team, get_team_players_season_data
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64


@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.is_dummy = False  # Ensure the team is not a dummy
            team.save()

            # Replace a dummy team with the newly created team
            if replace_dummy_team(team):
                return redirect('game:home')
            else:
                form.add_error(None, "No dummy team found to replace.")
    else:
        form = TeamCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'team/create_team.html', context)


def team_squad(request):
    team = get_object_or_404(Team, user=request.user)
    players_data = get_team_players_season_data(team)

    context = {
        'team': team,
        'players_data': players_data
    }

    return render(request, 'team/squad.html', context)


def line_up(request):
    team_players = Player.objects.filter(team=request.user.team)
    starting_players = team_players.filter(is_starting=True).order_by('position_id')
    available_players = team_players.filter(is_starting=False).order_by('position_id')
    print(f'ap: {available_players}')

    available_players_data = [get_player_data(player) for player in available_players]
    print(f'apd: {available_players_data}')
    team_tactics = TeamTactics.objects.filter(team=request.user.team).first()

    return render(request, 'team/line_up.html', {
        'starting_players': starting_players,
        'available_players': available_players_data,
        'team_tactics': team_tactics,
        'tactics': Tactics.objects.all()
    })


def select_tactics(request):
    tactic_id = request.POST.get('tactic_id')
    if tactic_id:
        Player.objects.filter(team=request.user.team, is_starting=True).update(is_starting=False)
        team_tactics, created = TeamTactics.objects.update_or_create(team=request.user.team,
                                                                     defaults={'tactic_id': tactic_id})
    return redirect('teams:line_up')


@require_POST
def add_starting_player(request):
    player_id = request.POST.get("player_id")

    team_tactics = TeamTactics.objects.filter(team=request.user.team).first()

    if not team_tactics:
        messages.error(request, "No tactics found for your team.")
        return redirect('teams:line_up')

    if player_id:
        try:
            player = Player.objects.get(id=player_id)

            starting_players = Player.objects.filter(is_starting=True, team=request.user.team)
            position_count = {
                'GK': 0,
                'DF': 0,
                'MF': 0,
                'ATT': 0,
            }

            for sp in starting_players:
                position_count[sp.position.abbr] += 1

            if len(starting_players) >= 11:
                messages.error(request, "Cannot add more than 11 players to the starting lineup.")
                return redirect('teams:line_up')

            if player.position.abbr == 'GK' and position_count['GK'] < team_tactics.tactic.num_goalkeepers:
                player.is_starting = True
            elif player.position.abbr == 'DF' and position_count['DF'] < team_tactics.tactic.num_defenders:
                player.is_starting = True
            elif player.position.abbr == 'MF' and position_count['MF'] < team_tactics.tactic.num_midfielders:
                player.is_starting = True
            elif player.position.abbr == 'ATT' and position_count['ATT'] < team_tactics.tactic.num_forwards:
                player.is_starting = True
            else:
                messages.error(request,
                               f"Cannot add {player.first_name} {player.last_name} to the starting lineup. Maximum limit reached for position.")
            return redirect('teams:line_up')

            player.save()
            messages.success(request, f"{player.first_name} {player.last_name} was added to the starting lineup.")

        except Player.DoesNotExist:
            messages.error(request, "Player not found.")
            return redirect('teams:line_up')

    return redirect('teams:line_up')

@require_POST
def remove_starting_player(request):
    player_id = request.POST.get("player_id")
    if player_id:
        try:
            player = Player.objects.get(id=player_id)
            player.is_starting = False
            player.save()
        except Player.DoesNotExist:
            pass
    return redirect('teams:line_up')

def team_stats(request):
    team = Team.objects.get(id=request.user.team.id)  # Assuming the user is linked to a team
    season_stats = TeamSeasonStats.objects.filter(team=team)

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
        'Points': []
    }

    for stat in season_stats:
        season_label = f"{stat.season.year} - {stat.season.season_number}"
        stats_data["Year"].append(stat.season.year)
        stats_data["Season"].append(stat.season.season_number)
        stats_data["Matches"].append(stat.matches)
        stats_data["Wins"].append(stat.wins)
        stats_data["Draws"].append(stat.draws)
        stats_data["Losses"].append(stat.losses)
        stats_data["Goals Scored"].append(stat.goalscored)
        stats_data["Goals Against"].append(stat.goalconceded)
        stats_data["Goal Difference"].append(stat.goaldifference)
        stats_data['Points'].append(stat.points)

        df = pd.DataFrame(stats_data)

        plt.figure(figsize=(10, 5))
        plt.plot(df["Season"], df["Wins"], label="Wins", marker='o')
        plt.plot(df["Season"], df["Draws"], label="Draws", marker='o')
        plt.plot(df["Season"], df["Losses"], label="Losses", marker='o')
        plt.title(f"{team.name} Performance Over Seasons")
        plt.xlabel("Season")
        plt.xticks(rotation=45)
        plt.ylabel("Number of Matches")
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img = base64.b64encode(buf.read()).decode('utf-8')

    context = {
        'team': team,
        'season_stats': season_stats,
        'img': img
    }

    return render(request, 'team/team_stats.html', context)

def delete_team(team_id):
    team = get_object_or_404(Team, id=team_id)
    team.delete()
    return redirect('team_list')

def get_consonants(name):
    vowels = "AEIOUaeiou"
    consonants = [char for char in name if char not in vowels and char.isalpha()]  # Filter consonants
    return ''.join(consonants[:3]).upper()  # Get first 3 consonants and make them uppercase
