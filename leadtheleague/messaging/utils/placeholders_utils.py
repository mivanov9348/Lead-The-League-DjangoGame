from datetime import date, timedelta
from europeancups.models import EuropeanCupSeason
from fixtures.models import LeagueFixture


def get_new_season_placeholders(season):
    return {
        'season_number': season.season_number,
        'year': season.year
    }


def get_new_manager_placeholders(user, team):
    return {
        'user_name': user.username,
        'team_name': team.name,
    }


def get_european_cup_champion_placeholder():
    latest_season = EuropeanCupSeason.objects.filter(champion__isnull=False).order_by('-season').first()
    if not latest_season:
        raise ValueError("No European Cup Champion found in the database.")
    return {'team_name': latest_season.champion.name}


def get_free_agent_transfer_placeholders(player, team):

    return {
        'player_name': f"{player.first_name} {player.last_name}",
        'team_name': team.name
    }


def get_new_coach_placeholders(coach, team):
    if not team.is_active:
        raise ValueError(f"The team {team.name} is not active.")

    return {
        'coach_name': f"{coach.first_name} {coach.last_name}",
        'team_name': team.name
    }


def get_league_matchday_placeholders(league_season):
    yesterday = date.today() - timedelta(days=1)
    # temporary
    today = date.today() + timedelta(days=2)
    fixtures = LeagueFixture.objects.filter(
        league_season=league_season,
        date=today,
        is_finished=True
    ).select_related('home_team', 'away_team')

    if not fixtures.exists():
        raise ValueError(f"No finished matches found for {league_season.league.name} on {today}.")

    match_results = "\n".join([
        f"{fixture.home_team.name} {fixture.home_goals} - {fixture.away_goals} {fixture.away_team.name}"
        for fixture in fixtures
    ])

    return {
        'league_name': league_season.league.name,
        'match_results': match_results
    }
