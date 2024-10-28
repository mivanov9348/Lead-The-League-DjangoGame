from django.shortcuts import get_object_or_404

from leagues.models import League, Division, DivisionTeam


def get_leagues_and_divisions():
    leagues = League.objects.prefetch_related('division_set').all()
    return leagues


def get_selected_league_and_division(league_id, division_id):
    league = get_object_or_404(League, id=league_id)
    division = get_object_or_404(Division, id=division_id, league=league)
    standings = DivisionTeam.objects.filter(division=division)

    return league, division

def get_standings_for_division(division):
    return DivisionTeam.objects.filter(division=division)
