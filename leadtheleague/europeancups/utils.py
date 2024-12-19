import random
from django.db.models import Max
from europeancups.models import EuropeanCupSeason, Group, GroupTeam, EuropeanCupTeam, KnockoutStage, KnockoutTeam
from fixtures.models import EuropeanCupFixture
from game.models import MatchSchedule
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

from django.db import transaction

def generate_group_fixtures(group):
    print(f"Generating fixtures for group: {group.name}")

    # Fetch teams in the group
    group_teams = list(GroupTeam.objects.filter(group=group))
    teams = [team.team for team in group_teams]

    if len(teams) < 2:
        raise ValueError("Group must have at least two teams to generate fixtures.")

    if len(teams) % 2 != 0:
        teams.append(None)  # Add a bye if odd number of teams

    # Calculate number of rounds
    num_rounds = len(teams) - 1
    total_rounds = 2 * num_rounds

    # Fetch shared dates across all groups
    if not hasattr(generate_group_fixtures, "shared_dates"):
        generate_group_fixtures.shared_dates = list(
            MatchSchedule.objects.filter(
                event_type='euro',
                is_euro_cup_day_assigned=False,
            ).order_by('date')[:total_rounds]
        )
    match_schedule = generate_group_fixtures.shared_dates

    if len(match_schedule) < total_rounds:
        raise ValueError(f"Not enough match dates. Needed: {total_rounds}, available: {len(match_schedule)}.")

    max_fixture_number = EuropeanCupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0
    next_fixture_number = max_fixture_number + 1
    fixtures = []

    # Helper function for rotating teams
    def rotate_teams(teams):
        return [teams[0]] + [teams[-1]] + teams[1:-1]

    # Generate fixtures
    with transaction.atomic():
        match_date_index = 0

        # Generate first half (normal order)
        for round_num in range(num_rounds):
            round_matches = [
                (teams[i], teams[-(i + 1)]) for i in range(len(teams) // 2) if teams[i] and teams[-(i + 1)]
            ]
            match_date = match_schedule[match_date_index]

            for home_team, away_team in round_matches:
                fixtures.append(EuropeanCupFixture(
                    fixture_number=next_fixture_number,
                    home_team=home_team,
                    away_team=away_team,
                    group=group,
                    european_cup_season=group.european_cup_season,
                    round_stage="Group Stage",
                    round_number=round_num + 1,
                    date=match_date.date,
                ))
                next_fixture_number += 1

            teams = rotate_teams(teams)
            match_date_index += 1

        # Generate reverse fixtures (second half)
        for round_num in range(num_rounds):
            round_matches = [
                (fixture.away_team, fixture.home_team)
                for fixture in fixtures[round_num * (len(teams) // 2):(round_num + 1) * (len(teams) // 2)]
            ]
            match_date = match_schedule[match_date_index]

            for home_team, away_team in round_matches:
                fixtures.append(EuropeanCupFixture(
                    fixture_number=next_fixture_number,
                    home_team=home_team,
                    away_team=away_team,
                    group=group,
                    european_cup_season=group.european_cup_season,
                    round_stage="Group Stage",
                    round_number=num_rounds + round_num + 1,
                    date=match_date.date,
                ))
                next_fixture_number += 1

            match_date_index += 1

        # Save all fixtures in bulk
        EuropeanCupFixture.objects.bulk_create(fixtures)

        # Mark shared dates as assigned only once
        if not hasattr(generate_group_fixtures, "shared_dates_assigned"):
            for match_date in match_schedule:
                match_date.is_euro_cup_day_assigned = True
                match_date.save()
            generate_group_fixtures.shared_dates_assigned = True

    print(f"Successfully created {len(fixtures)} fixtures for group {group.name}.")
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

        random.shuffle(advancing_teams)

        # Създаваме нов KnockoutStage
        knockout_stage = KnockoutStage.objects.create(
            european_cup_season=european_cup_season,
            stage_name=stage_name,
            stage_order=stage_order
        )

        fixtures = []
        max_fixture_number = EuropeanCupFixture.objects.aggregate(
            Max('fixture_number')
        )['fixture_number__max'] or 0
        next_fixture_number = max_fixture_number + 1

        # Намираме свободни дати за мачовете
        match_schedule = MatchSchedule.objects.filter(
            season=european_cup_season.season,
            event_type='euro',
            is_euro_cup_day_assigned=False,  # Свободно място
        ).order_by('date')

        if len(match_schedule) < len(advancing_teams) // 2:
            raise ValueError("Not enough match dates available for knockout round.")

        schedule_index = 0

        # Създаваме двойки за нокаут рунда
        for i in range(0, len(advancing_teams), 2):
            home_team = advancing_teams[i].team
            away_team = advancing_teams[i + 1].team

            match_date = match_schedule[schedule_index]
            schedule_index += 1

            fixtures.append(EuropeanCupFixture(
                fixture_number=next_fixture_number,
                home_team=home_team,
                away_team=away_team,
                european_cup_season=european_cup_season,
                round_stage=stage_name,
                round_number=stage_order,
                date=match_date.date,
            ))

            # Обновяваме `is_euro_cup_day_assigned` за съответния ден
            match_date.is_euro_cup_day_assigned = True
            match_date.save()

            next_fixture_number += 1

            # Добавяме отборите в KnockoutStage
            KnockoutTeam.objects.bulk_create([
                KnockoutTeam(knockout_stage=knockout_stage, team=home_team),
                KnockoutTeam(knockout_stage=knockout_stage, team=away_team),
            ])

        # Създаваме всички фикстури наведнъж
        EuropeanCupFixture.objects.bulk_create(fixtures)

        return f"Knockout stage '{stage_name}' created with {len(fixtures)} matches."



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

