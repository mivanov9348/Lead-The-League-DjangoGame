from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from cups.utils.get_cups_utils import promote_cup_champions_to_europe
from europeancups.models import EuropeanCupSeason, EuropeanCupTeam, KnockoutStage, EuropeanCup
from fixtures.models import EuropeanCupFixture
from game.utils.get_season_stats_utils import get_current_season
from leagues.utils import promote_league_teams_to_europe
from match.models import Match
from messaging.utils.category_messages_utils import create_european_cup_champion_message
from teams.models import Team
from vault.utils.team_all_stats import add_euro_cup_title

def get_current_european_cup_season():
    current_season = get_current_season()
    euro_season = EuropeanCupSeason.objects.filter(season=current_season).first()
    if not euro_season:
        raise ValueError("No European Cup season found for the current season.")
    print(f"Current European Cup season: {euro_season}")
    return euro_season

def get_current_knockout_stage_order(current_euro_season):
    current_stage = KnockoutStage.objects.filter(
        european_cup_season=current_euro_season,
        is_played=False
    ).order_by('stage_order').first()

    if not current_stage:
        print("No unplayed knockout stage found.")
        return None

    print(f"Current knockout stage: {current_stage} (Stage order: {current_stage.stage_order})")
    return current_stage


def are_knockout_stage_matches_finished(euro_season, stage_order):
    try:
        knockout_stage = euro_season.knockout_stages.get(stage_order=stage_order)
    except KnockoutStage.DoesNotExist:
        return True

    european_cup_fixture_type = ContentType.objects.get_for_model(EuropeanCupFixture)

    matches = Match.objects.filter(
        fixture_content_type=european_cup_fixture_type,
        fixture_object_id__in=EuropeanCupFixture.objects.filter(knockout_stage=knockout_stage).values_list('id', flat=True),
        is_played=False
    )

    return not matches.exists()


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

def check_and_update_euro_cup_season_status(euro_cup_season):
    if not euro_cup_season.is_group_stage_finished:
        groups = euro_cup_season.groups.all()
        all_groups_finished = all(
            group.groupteam_set.filter(matches=euro_cup_season.teams_per_group - 1).count() == euro_cup_season.teams_per_group
            for group in groups
        )
        if all_groups_finished:
            euro_cup_season.is_group_stage_finished = True

    knockout_stages = euro_cup_season.knockout_stages.all()
    all_knockout_stages_played = all(stage.is_played for stage in knockout_stages)

    if euro_cup_season.is_group_stage_finished and all_knockout_stages_played:
        euro_cup_season.is_euro_cup_finished = True
        euro_cup_season.save()
        return f"Season '{euro_cup_season}' is finished."

    euro_cup_season.save()
    return f"Season '{euro_cup_season}' is not yet finished."

def europe_promotion(new_season):
    european_cups = EuropeanCup.objects.all()
    new_euro_cup_season = EuropeanCupSeason.objects.filter(season=new_season).first()
    if not new_euro_cup_season:
        raise ValueError(f"No European Cup Season found for season {new_season}.")

    with transaction.atomic():
        total_added_teams = 0

        cup_champions = promote_cup_champions_to_europe(new_season, new_euro_cup_season)
        print(f'cup champions: {cup_champions}')
        total_added_teams += len(cup_champions)

        league_teams = promote_league_teams_to_europe(new_euro_cup_season,cup_champions)
        print(f'league_teams: {league_teams}')

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


def finalize_euro_cup(european_cup_season, match):
    fixture = EuropeanCupFixture.objects.filter(
        home_team=match.home_team,
        away_team=match.away_team,
        season=match.season,
        is_finished=True
    ).first()

    if not fixture:
        raise ValueError("No completed fixture found for the given match.")

    winner_team = fixture.winner
    if not winner_team:
        raise ValueError("Cannot finalize European Cup season without a winner.")

    european_cup_season.champion = winner_team
    add_euro_cup_title(winner_team)
    european_cup_season.current_phase = 'finished'
    european_cup_season.is_euro_cup_finished = True
    european_cup_season.save()
    create_european_cup_champion_message(european_cup_season, winner_team)

    print(f"European Cup {european_cup_season.cup.name} for season {european_cup_season.season} is completed.")
    print(f"The champion is {winner_team.name}.")
