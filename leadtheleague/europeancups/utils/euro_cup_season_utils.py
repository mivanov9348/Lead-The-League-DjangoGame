from django.db import transaction
from europeancups.models import EuropeanCupSeason, EuropeanCupTeam
from teams.models import Team

def create_season_european_cup(cup, season, total_teams, groups_count, teams_per_group, teams_qualify_from_group):
    with transaction.atomic():
        if total_teams != groups_count * teams_per_group:
            raise ValueError("Count of the teams is not equal to groups_count * teams_per_group!")

        european_cup_season = EuropeanCupSeason.objects.create(
            cup=cup,
            season=season,
            total_teams=total_teams,
            groups_count=groups_count,
            teams_per_group=teams_per_group,
            total_teams_qualify_from_group=teams_qualify_from_group
        )

        return european_cup_season

# АAdd teams to europeancup
def add_team_to_european_cup(team, european_cup_season):
    if EuropeanCupTeam.objects.filter(team=team, european_cup_season=european_cup_season).exists():
        raise ValueError(f"The team {team.name} is currently added to {european_cup_season}.")

    EuropeanCupTeam.objects.create(
        team=team,
        european_cup_season=european_cup_season
    )
    return f"The team {team.name} is added for season {european_cup_season}."

def populate_remaining_teams(european_cup_season):
    total_teams = european_cup_season.total_teams

    current_team_count = EuropeanCupTeam.objects.filter(european_cup_season=european_cup_season).count()

    remaining_spots = total_teams - current_team_count

    if remaining_spots <= 0:
        return "All teams are added!"

    excluded_countries = ["Bulgaria", "Germany", "England", "Spain", "Italy"]

    inactive_teams = Team.objects.filter(
        is_active=False
    ).exclude(
        id__in=EuropeanCupTeam.objects.filter(
            european_cup_season=european_cup_season
        ).values_list('team_id', flat=True)
    ).exclude(
        nationality__name__in=excluded_countries
    )[:remaining_spots]

    if not inactive_teams.exists():
        raise ValueError("Not enough teams.")

    for team in inactive_teams:
        EuropeanCupTeam.objects.create(
            team=team,
            european_cup_season=european_cup_season
        )

    return "Added successfully!"

