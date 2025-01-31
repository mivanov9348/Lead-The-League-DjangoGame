from datetime import date, timedelta
from decimal import Decimal
from dateutil.utils import today
from cups.models import SeasonCup
from europeancups.models import EuropeanCupSeason
from fixtures.models import LeagueFixture, CupFixture
from leagues.models import LeagueSeason

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

def get_team_to_team_transfer_placeholder(player, from_team, to_team, transfer_fee):
    transfer_fee = Decimal(transfer_fee)
    return {
        'player_name': f'{player.first_name} {player.last_name}',
        'old_team_name': from_team.name,
        'new_team_name': to_team.name,
        'transfer_fee': f"${transfer_fee:,}"
    }

def get_send_offer_placeholder(player, from_team, to_team, offer_amount):
    offer_amount = Decimal(offer_amount).quantize(Decimal("0.01"))
    return {
        'player_name': f'{player.first_name} {player.last_name}',
        'from_team_name': from_team.name,
        'to_team_name': to_team.name,
        'offer_amount': f"${offer_amount:,}"
    }

def get_free_agent_transfer_placeholders(player, team):
    return {
        'player_name': f"{player.first_name} {player.last_name}",
        'team_name': team.name
    }

def get_release_player_placeholders(player, team):
    return {
        'player_name': f"{player.first_name} {player.last_name}",
        'team_name': team.name
    }


def get_new_coach_placeholders(coach, team):

    return {
        'coach_name': f"{coach.first_name} {coach.last_name}",
        'team_name': team.name
    }


def get_league_matchday_placeholders(league_season):
    yesterday = date.today() - timedelta(days=1)
    # temporary
    today = date.today() + timedelta(days=1)
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


def get_cup_matchday_placeholders(season_cup):
    fixtures = CupFixture.objects.filter(
        season_cup=season_cup,
        # date=today,
        is_finished=True
    ).select_related('home_team', 'away_team')

    if not fixtures.exists():
        raise ValueError(f"No finished matches found for {season_cup.cup.name} on {today}.")

    match_results = "\n".join([
        f"{fixture.home_team.name} {fixture.home_goals} - {fixture.away_goals} {fixture.away_team.name}"
        for fixture in fixtures
    ])

    return {
        'cup': season_cup.name,
        'match_results': match_results
    }

def get_stadium_upgrade_placeholders(team, stadium_name, tier_name):
    return {
        'team_name': team.name,
        'stadium_name': stadium_name,
        'tier_name': tier_name,
    }
