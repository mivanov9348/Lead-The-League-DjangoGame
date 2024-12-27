from django.db import transaction
from cups.utils.get_cups_utils import promote_cup_champions_to_europe
from europeancups.models import EuropeanCupSeason, EuropeanCupTeam, KnockoutStage, EuropeanCup
from fixtures.models import EuropeanCupFixture
from game.utils.get_season_stats_utils import get_current_season
from leagues.models import League
from leagues.utils import promote_league_teams_to_europe
from messaging.utils.category_messages_utils import create_european_cup_champion_message
from teams.models import Team


def generate_european_cups_season(season):
    european_cups = EuropeanCup.objects.all()
    for euro_cup in european_cups:
        if not EuropeanCupSeason.objects.filter(cup=euro_cup, season=season).exists():
            EuropeanCupSeason.objects.create(cup=euro_cup, season=season)


# АAdd teams to europeancup
def add_team_to_european_cup(team, european_cup_season):
    if EuropeanCupTeam.objects.filter(team=team, european_cup_season=european_cup_season).exists():
        raise ValueError(f"The team {team.name} is currently added to {european_cup_season}.")

    EuropeanCupTeam.objects.create(
        team=team,
        european_cup_season=european_cup_season
    )
    return f"The team {team.name} is added for season {european_cup_season}."


def europe_promotion(new_season):
    european_cups = EuropeanCup.objects.all()
    top_leagues = League.objects.filter(is_top_league=True)
    new_euro_cup_season = EuropeanCupSeason.objects.filter(season=new_season).first()
    if not new_euro_cup_season:
        raise ValueError(f"No European Cup Season found for season {new_season}.")

    with transaction.atomic():
        total_added_teams = 0

        cup_champions = promote_cup_champions_to_europe(new_season, new_euro_cup_season, european_cups)
        total_added_teams += len(cup_champions)

        league_teams = promote_league_teams_to_europe(new_season, new_euro_cup_season, european_cups, cup_champions)
        total_added_teams += len(league_teams)

        fill_remaining_spots(new_euro_cup_season, total_added_teams)


def fill_remaining_spots(new_european_cup_season, total_added_teams):
    total_teams_needed = new_european_cup_season.total_teams
    remaining_spots = total_teams_needed - total_added_teams

    if remaining_spots > 0:
        excluded_countries = ["Bulgaria", "Germany", "England", "Spain", "Italy"]
        inactive_teams = Team.objects.filter(
            is_active=False
        ).exclude(
            id__in=EuropeanCupTeam.objects.filter(
                european_cup_season=new_european_cup_season
            ).values_list('team_id', flat=True)
        ).exclude(
            nationality__name__in=excluded_countries
        )[:remaining_spots]

        if not inactive_teams.exists():
            raise ValueError("Not enough teams to fill remaining spots.")

        for team in inactive_teams:
            EuropeanCupTeam.objects.create(
                team=team,
                european_cup_season=new_european_cup_season
            )

        print(f"Added {len(inactive_teams)} remaining teams to complete the list for {new_european_cup_season}.")


def set_european_cup_season_champion():
    current_season = get_current_season()
    european_cup_season = EuropeanCupSeason.objects.filter(season=current_season).first()

    final_stage = KnockoutStage.objects.filter(
        european_cup_season=european_cup_season,
        is_final=True
    ).first()

    if not final_stage:
        raise ValueError("Final stage not found for the current European Cup season.")

    final_fixture = EuropeanCupFixture.objects.filter(
        european_cup_season=european_cup_season,
        knockout_stage=final_stage,
        is_finished=True
    ).first()

    if not final_fixture:
        raise ValueError("No finished final match found for the current European Cup season.")

    champion = final_fixture.winner
    if not champion:
        raise ValueError("No winner found for the final match.")

    european_cup_season.champion = champion
    european_cup_season.save()
    create_european_cup_champion_message()
    return champion
