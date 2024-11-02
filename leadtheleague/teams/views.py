from django.shortcuts import render, get_object_or_404, redirect
from .forms import TeamCreationForm
from players.models import Player, PlayerAttribute
from teams.models import Team
from django.contrib.auth.decorators import login_required
from .utils import replace_dummy_team, get_team_players_season_data


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


@login_required()
def line_up(request):
    players = Player.objects.filter(team=request.user.team).values('id', 'first_name', 'position')
    print(players)
    players_list = list(players)  # Convert to list for JSON serialization
    return render(request, 'team/line_up.html', {'players': players_list})


@login_required
def save_lineups(request):
    if request.method == 'POST':
        # Get selected player IDs from the form
        selected_player_ids = request.POST.getlist('selected_players')
        print(selected_player_ids)
        # Reset is_starting to False for all players in the user's team
        user_team_players = Player.objects.filter(team=request.user.team)
        user_team_players.update(is_starting=False)

        # Set is_starting to True for selected players
        starting_players = user_team_players.filter(id__in=selected_player_ids)
        starting_players.update(is_starting=True)

        # Redirect back to the lineup page after saving
        return redirect('team/line_up.html')  # Update 'lineup_view' with the actual name of your lineup URL

        # Redirect to lineup page if accessed via GET
    return redirect('team/line_up.html')


def team_stats(request):
    team = Team.objects.get(id=request.user.team.id)  # Assuming the user is linked to a team

    context = {
        'team': team,
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
