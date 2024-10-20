from django.shortcuts import render, get_object_or_404
from .models import Team

# Create your views here.
def team_squad(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    players = team.players.all()
    return render(request, 'teams/team_squad', {'team':team, 'players':players})