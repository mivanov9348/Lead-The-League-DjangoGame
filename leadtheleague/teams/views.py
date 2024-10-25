from django.shortcuts import render, get_object_or_404, redirect
from players.utils import generate_team_players
from .forms import TeamCreationForm
from players.models import Player, Attribute, PlayerAttribute
from teams.models import Team
from django.contrib.auth.decorators import login_required

@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.save()
            generate_team_players(team)
            return redirect('game:mainmenu')
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
        # Връщаме всички играчи с is_starting = False, преди да обработим новите избраници
        Player.objects.update(is_starting=False)

        # Събираме избраните играчи от POST данните
        starting_players = [
            request.POST.get('goalkeeper'),
            *[request.POST.get(f'defender{i}') for i in range(1, 5)],
            *[request.POST.get(f'midfielder{i}') for i in range(1, 5)],
            *[request.POST.get(f'attacker{i}') for i in range(1, 3)],
        ]

        # Актуализираме is_starting = True само за избраните играчи
        for player_id in starting_players:
            if player_id:  # Ако играчът е избран
                Player.objects.filter(id=player_id).update(is_starting=True)

        return redirect('some_success_url')  # Може да се добави правилно пренасочване след успешна заявка

    # Зареждаме всички играчи по категории
    goalkeepers = Player.objects.filter(position__position_name='Goalkeeper')
    defenders = Player.objects.filter(position__position_name='Defender')
    midfielders = Player.objects.filter(position__position_name='Midfielder')
    attackers = Player.objects.filter(position__position_name='Attacker')

    # Всички играчи, които не са в starting XI
    substitutes = Player.objects.filter(is_starting=False)

    # Генерираме данни за заместници с техните атрибути
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
    if request.method == "POST":
        goalkeeper_id = request.POST.get('goalkeeper')
        defenders_ids = request.POST.getlist('defenders')
        midfielders_ids = request.POST.getlist('midfielders')
        attackers_ids = request.POST.getlist('attackers')

        if goalkeeper_id:
            Player.objects.filter(id=goalkeeper_id).update(is_started=True)

        Player.objects.filter(id__in=defenders_ids).update(is_started=True)
        Player.objects.filter(id__in=midfielders_ids).update(is_started=True)
        Player.objects.filter(id__in=attackers_ids).update(is_started=True)

        return redirect('line_up.html')

    return render(request, 'team/line_up.html')


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
