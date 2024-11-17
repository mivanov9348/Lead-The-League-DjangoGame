from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
import json

from game.utils import get_current_season
from players.utils import get_player_season_stats_by_team
from .forms import TeamCreationForm
from players.models import Player
from teams.models import Team, TeamTactics, Tactics, TeamSeasonStats
from django.contrib.auth.decorators import login_required
from .utils import replace_dummy_team, get_team_players_season_data, create_team_performance_chart


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


def squad(request):
    team = get_object_or_404(Team, user=request.user)
    players_data = get_team_players_season_data(team)
    print(players_data)
    context = {
        'team': team,
        'players_data': players_data
    }

    return render(request, 'team/squad.html', context)


def team_stats(request):
    team = Team.objects.get(id=request.user.team.id)  # Assuming the user is linked to a team
    season_stats = TeamSeasonStats.objects.filter(team=team)

    img = create_team_performance_chart(season_stats, team.name)

    context = {
        'team': team,
        'season_stats': season_stats,
        'img': img
    }

    return render(request, 'team/team_stats.html', context)


@csrf_exempt
def line_up(request):
    user_team = get_object_or_404(Team, user=request.user)
    season = get_current_season()

    players = get_player_season_stats_by_team(user_team, season)

    startingPlayers = [
        player for player in players
        if player['player_data']['player']['is_starting']  # Ако играчът е титулярен
    ]
    reservePlayers = [
        player for player in players
        if not player['player_data']['player']['is_starting']  # Ако играчът не е титулярен
    ]

    print(reservePlayers)

    positions = {
        "GK": ["GK"],
        "DF": ["DF", "DF", "DF", "DF"],
        "MF": ["MF", "MF", "MF", "MF"],
        "ATT": ["ATT", "ATT"],
    }

    slots = range(1, 12)

    context = {
        'slots': slots,
        'startingPlayers': startingPlayers,
        'reservePlayers': reservePlayers,
        'positions': positions,
        'team': user_team
    }

    return render(request, "team/line_up.html", context)


def modify_lineup(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        player_id = request.POST.get('player_id')

        # Handle adding player to lineup
        if action == 'add' and player_id:
            player = Player.objects.get(id=player_id)
            player.is_starting = True
            player.save()

        # Handle removing player from lineup
        elif action == 'remove' and player_id:
            player = Player.objects.get(id=player_id)
            player.is_starting = False
            player.save()

        return redirect('teams:line_up')

    return redirect('teams:line_up')
