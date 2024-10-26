from django.shortcuts import render, get_object_or_404, redirect
from leagues.models import League
from players.utils import generate_team_players
from .forms import TeamCreationForm
from players.models import Player, Attribute, PlayerAttribute
from teams.models import Team
from django.contrib.auth.decorators import login_required
from leagues.models import Division, DivisionTeam

@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.save()

            league = League.objects.first()
            if league:
                division = Division.objects.filter(league=league).first()
                if division:
                    DivisionTeam.objects.create(division=division, team=team, is_dummy=False)

            generate_team_players(team)
            return redirect('game:home')
    else:
        form = TeamCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'team/create_team.html', context)


def team_squad(request):
    team = get_object_or_404(Team, user=request.user)
    players = Player.objects.filter(team=team)

    # Sorting Logic
    sort_by = request.GET.get('sort')
    if sort_by == 'name':
        players = players.order_by('first_name', 'last_name')
    elif sort_by == 'age':
        players = players.order_by('age')
    elif sort_by == 'nationality':
        players = players.order_by('nationality__name')
    elif sort_by == 'position':
        players = players.order_by('position__name')
    elif sort_by == 'price':
        players = players.order_by('price')

    player_data = []
    for player in players:
        attributes = PlayerAttribute.objects.filter(player=player)  # Get attributes for the player
        attribute_values = {attr.attribute.name: attr.value for attr in attributes}  # Map attribute name to its value
        player_data.append({
            'player': player,
            'attributes': attribute_values,
        })

    context = {
        'team': team,
        'player_data': player_data
    }

    return render(request, 'team/squad.html', context)


@login_required()
def line_up(request):
    if request.method == 'POST':
        Player.objects.update(is_starting=False)

        # Събираме избраните играчи от POST данните
        starting_players = [
            request.POST.get('goalkeeper'),
            *[request.POST.get(f'defender{i}') for i in range(1, 5)],
            *[request.POST.get(f'midfielder{i}') for i in range(1, 5)],
            *[request.POST.get(f'attacker{i}') for i in range(1, 3)],
        ]

        for player_id in starting_players:
            if player_id:
                Player.objects.filter(id=player_id).update(is_starting=True)

        return redirect('team/line_up.html')

    goalkeepers = Player.objects.filter(position__position_name='Goalkeeper')
    defenders = Player.objects.filter(position__position_name='Defender')
    midfielders = Player.objects.filter(position__position_name='Midfielder')
    attackers = Player.objects.filter(position__position_name='Attacker')

    substitutes = Player.objects.filter(is_starting=False)

    substitute_data = []
    for player in substitutes:
        attributes = PlayerAttribute.objects.filter(player=player)
        attribute_values = {attr.attribute.name: attr.value for attr in attributes}
        substitute_data.append({
            'player': player,
            'attributes': attribute_values,
        })

    context = {
        'goalkeepers': goalkeepers,
        'defenders': defenders,
        'midfielders': midfielders,
        'attackers': attackers,
        'substitutes': substitutes,
        'substitute_data': substitute_data,
    }
    return render(request, 'team/line_up.html', context)



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
