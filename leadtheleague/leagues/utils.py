from teams.models import TeamSeasonStats, Team
from .models import League

def get_all_leagues():
    return League.objects.all()

def get_selected_league(league_id):
    league = League.objects.filter(id=league_id).first()
    return league

def get_standings_for_league(league):
    return TeamSeasonStats.objects.filter(
        league=league
    ).select_related('team').order_by('-points', '-goalscored', 'goalconceded')

def get_teams_by_league(league_id):
    return Team.objects.filter(league_id=league_id) if league_id else Team.objects.none()