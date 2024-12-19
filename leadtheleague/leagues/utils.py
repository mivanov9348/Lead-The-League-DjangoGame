from teams.models import Team
from .models import League, LeagueSeason, LeagueTeams


def get_all_leagues():
    return League.objects.all()

def get_all_season_leagues(season):
    return LeagueSeason.objects.filter(season=season)


def get_selected_league(league_id):
    league = League.objects.filter(id=league_id).first()
    return league


def get_standings_for_league(league):
    league_season = LeagueSeason.objects.filter(
        league=league,
        is_completed=False
    ).order_by('-season__year').first()

    if not league_season:
        return []

    return LeagueTeams.objects.filter(
        league_season=league_season
    ).select_related('team').order_by(
        '-points', '-goaldifference', '-goalscored', 'goalconceded'
    )


def get_teams_by_league(league_id):
    return Team.objects.filter(league_id=league_id) if league_id else Team.objects.none()


def populate_league_teams_from_json(league_season, json_data):
    league_name = league_season.league.name
    if league_name not in json_data:
        return f"No data for {league_name} in the JSON file."

    teams = json_data[league_name]
    for team_data in teams:
        team, _ = Team.objects.get_or_create(
            name=team_data["name"],
            defaults={
                "abbreviation": team_data["name"][:3].upper(),
                "reputation": team_data["reputation"],
                "nationality": league_season.league.nationality,
            },
        )

        LeagueTeams.objects.get_or_create(
            league_season=league_season,
            team=team,
            defaults={
                "matches": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goalscored": 0,
                "goalconceded": 0,
                "goaldifference": 0,
                "points": 0,
            },
        )
    return f"Teams populated for {league_name}."