import random
from datetime import timedelta

from django.db.models import Max
from django.utils.timezone import now

from europeancups.models import EuropeanCupSeason, Group, GroupTeam, EuropeanCupTeam, KnockoutStage, KnockoutTeam
from fixtures.models import EuropeanCupFixture
from teams.models import Team
from django.db import transaction


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

def create_groups_for_season(european_cup_season):
    with transaction.atomic():
        total_teams = european_cup_season.total_teams
        groups_count = european_cup_season.groups_count
        teams_per_group = european_cup_season.teams_per_group

        teams = list(EuropeanCupTeam.objects.filter(european_cup_season=european_cup_season))

        if len(teams) != total_teams:
            raise ValueError(f"Expected {total_teams} teams, but found {len(teams)} in EuropeanCupTeam.")

        random.shuffle(teams)

        group_names = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:groups_count]

        for i in range(groups_count):
            group = Group.objects.create(
                european_cup_season=european_cup_season,
                name=group_names[i]
            )
            group_teams = teams[i * teams_per_group:(i + 1) * teams_per_group]
            for european_cup_team in group_teams:
                GroupTeam.objects.create(
                    group=group,
                    team=european_cup_team.team
                )

    return f"Groups created successfully for {european_cup_season}!"

def generate_group_fixtures(group):
    group_teams = list(GroupTeam.objects.filter(group=group))
    if len(group_teams) < 2:
        raise ValueError("Group must have at least two teams to generate fixtures.")

    max_fixture_number = EuropeanCupFixture.objects.aggregate(
        Max('fixture_number')
    )['fixture_number__max'] or 0
    next_fixture_number = max_fixture_number + 1

    fixtures = []

    teams = [team.team for team in group_teams]
    num_teams = len(teams)

    if num_teams % 2 != 0:
        teams.append(None)  # None представлява пропуск

    num_rounds = len(teams) - 1
    half_rounds = num_rounds

    for round_num in range(half_rounds):
        matches = []
        for i in range(num_teams // 2):
            home_team = teams[i]
            away_team = teams[-(i + 1)]

            if home_team and away_team:  # Пропускаме "bye"
                matches.append((home_team, away_team))

        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        for match in matches:
            home_team, away_team = match
            fixtures.append(EuropeanCupFixture(
                fixture_number=next_fixture_number,
                home_team=home_team,
                away_team=away_team,
                group=group,
                european_cup_season=group.european_cup_season,
                round_stage="Group Stage",
                round_number=round_num + 1,
                date=now().date() + timedelta(days=(round_num * 7)),
            ))
            next_fixture_number += 1

    reverse_round_start = num_rounds + 1
    for i, fixture in enumerate(fixtures[:]):
        fixtures.append(EuropeanCupFixture(
            fixture_number=next_fixture_number,
            home_team=fixture.away_team,
            away_team=fixture.home_team,
            group=group,
            european_cup_season=group.european_cup_season,
            round_stage="Group Stage",
            round_number=reverse_round_start + (i // (num_teams // 2)),
            date=fixture.date + timedelta(days=num_rounds * 7),
        ))
        next_fixture_number += 1

    EuropeanCupFixture.objects.bulk_create(fixtures)

    return f"Successfully created {len(fixtures)} fixtures for group {group.name}."

# Which Teams Advance
def advance_teams_from_groups(european_cup_season):
    teams_qualify_from_group = european_cup_season.total_teams_qualify_from_group

    with transaction.atomic():
        for group in Group.objects.filter(european_cup_season=european_cup_season):
            group_teams = GroupTeam.objects.filter(group=group).order_by(
                '-points', '-goals_difference', '-goals_for'
            )[:teams_qualify_from_group]

            for group_team in group_teams:
                european_cup_team = EuropeanCupTeam.objects.get(
                    team=group_team.team,
                    european_cup_season=european_cup_season
                )
                european_cup_team.is_eliminated = False
                european_cup_team.save()

        EuropeanCupTeam.objects.filter(
            european_cup_season=european_cup_season,
            is_eliminated=False
        ).exclude(
            id__in=EuropeanCupTeam.objects.filter(
                team__groupteam__group__european_cup_season=european_cup_season
            ).values_list('id', flat=True)
        ).update(is_eliminated=True)

    return f"Teams advancing to knockout stage are marked for {european_cup_season}."


# Draw Knockout Round
def draw_knockout_round(european_cup_season, stage_name, stage_order):
    with transaction.atomic():
        advancing_teams = list(
            EuropeanCupTeam.objects.filter(
                european_cup_season=european_cup_season,
                is_eliminated=False
            )
        )

        if len(advancing_teams) % 2 != 0:
            raise ValueError("Number of advancing teams must be even for knockout draw.")

        random.shuffle(advancing_teams)  # Разбъркваме отборите

        # Създаваме нов нокаут рунд
        knockout_stage = KnockoutStage.objects.create(
            european_cup_season=european_cup_season,
            stage_name=stage_name,
            stage_order=stage_order
        )

        for i in range(0, len(advancing_teams), 2):
            KnockoutTeam.objects.create(
                knockout_stage=knockout_stage,
                team=advancing_teams[i].team
            )
            KnockoutTeam.objects.create(
                knockout_stage=knockout_stage,
                team=advancing_teams[i + 1].team
            )

        return f"Knockout stage {stage_name} created with {len(advancing_teams) // 2} matches."


# АAdd team to europeancup
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

