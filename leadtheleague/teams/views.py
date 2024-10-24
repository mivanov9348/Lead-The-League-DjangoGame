import random as rand
from django.shortcuts import render, get_object_or_404, redirect
from players.utils import generate_team_players
from .forms import TeamCreationForm
from .models import Team, AdjectiveTeamNames, NounTeamNames
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
    return render(request, 'team/squad.html')

def team_list(request):
    teams = Team.objects.all()
    if request.method == 'POST':
        adjectives = list(AdjectiveTeamNames.objects.values_list('word', flat = True))
        nouns = list(NounTeamNames.objects.values_list('word', flat = True))

        if adjectives and nouns:
            team_name = f'{rand.choice(adjectives)} {rand.choice(nouns)}'
            team_abbr = get_consonants(team_name)
            new_team = Team.objects.create(name=team_name, abbr = team_abbr)
            return redirect('team_list')
    return render(request, 'team/team_list.html', {'teams':teams})

def line_up(request):
    return render(request, 'team/line_up.html')

def team_stats(request):
    return render(request, 'team/team_stats.html')

def delete_team(team_id):
    team = get_object_or_404(Team, id=team_id)
    team.delete()
    return redirect('team_list')

def get_consonants(name):
    vowels = "AEIOUaeiou"
    consonants = [char for char in name if char not in vowels and char.isalpha()]  # Filter consonants
    return ''.join(consonants[:3]).upper()  # Get first 3 consonants and make them uppercase
