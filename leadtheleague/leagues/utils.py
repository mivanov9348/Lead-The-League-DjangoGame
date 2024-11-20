from teams.models import TeamSeasonStats
from .models import League

def get_leagues_and_divisions():
    return League.objects.prefetch_related('division_set').all()

def get_selected_league_and_division(league_id, division_id):
    league = League.objects.filter(id=league_id).first()
    division = None
    if league:
        division = league.division_set.filter(id=division_id).first()
    return league, division

def get_standings_for_division(division):
    return TeamSeasonStats.objects.filter(
        league=division.league.id,
        division=division
    ).select_related('team').order_by('-points', '-goalscored', 'goalconceded')