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

def generate_group_fixtures(group):
    print(f"Generating fixtures for group: {group.name}")

    group_teams = list(GroupTeam.objects.filter(group=group))
    print(f"Teams in group {group.name}: {[team.team.name for team in group_teams]}")

    if len(group_teams) < 2:
        raise ValueError("Group must have at least two teams to generate fixtures.")

    max_fixture_number = EuropeanCupFixture.objects.aggregate(
        Max('fixture_number')
    )['fixture_number__max'] or 0
    next_fixture_number = max_fixture_number + 1
    print(f"Starting fixture number: {next_fixture_number}")

    fixtures = []

    teams = [team.team for team in group_teams]
    if len(teams) % 2 != 0:
        teams.append(None)  # None represents a bye
    print(f"Teams after adding bye (if needed): {[team.name if team else 'None' for team in teams]}")

    num_rounds = len(teams) - 1  # Number of rounds (round-robin algorithm)
    print(f"Number of rounds: {num_rounds}")

    # Fetch all available match dates for the tournament
    match_schedule = MatchSchedule.objects.filter(
        event_type='euro',
        is_euro_cup_day_assigned=False,
    ).order_by('date')

    print(f"Available match dates: {[date.date for date in match_schedule]}")

    if len(match_schedule) < 6 * group.european_cup_season.groups.count():
        raise ValueError("Not enough match dates available for all group fixtures.")

    # Assign fixtures to dates, cycling through the schedule as needed
    match_date_index = 0
    for round_num in range(num_rounds):
        print(f"Generating matches for round {round_num + 1}")
        matches = []
        for i in range(len(teams) // 2):
            home_team = teams[i]
            away_team = teams[-(i + 1)]
            if home_team and away_team:
                matches.append((home_team, away_team))

        print(f"Matches for round {round_num + 1}: {[(m[0].name, m[1].name) for m in matches]}")

        # Rotate teams for the next round (round-robin algorithm)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        print(f"Teams rotated for next round: {[team.name if team else 'None' for team in teams]}")

        # Assign a date to this round's matches
        match_date = match_schedule[match_date_index % len(match_schedule)]
        print(f"Date for round {round_num + 1}: {match_date.date}")

        for match in matches:
            print(f"Adding fixture: {match[0].name} vs {match[1].name} on {match_date.date}")
            fixtures.append(EuropeanCupFixture(
                fixture_number=next_fixture_number,
                home_team=match[0],
                away_team=match[1],
                group=group,
                european_cup_season=group.european_cup_season,
                round_stage="Group Stage",
                round_number=round_num + 1,
                date=match_date.date,
            ))
            next_fixture_number += 1

        match_date_index += 1

    # Reverse matches (second half of the rounds)
    reverse_round_start = num_rounds
    print(f"Generating reverse matches (rounds {reverse_round_start + 1} to {reverse_round_start + num_rounds})")
    for round_num in range(num_rounds):
        match_date = match_schedule[match_date_index % len(match_schedule)]
        print(f"Date for reverse round {round_num + 1}: {match_date.date}")

        for fixture in fixtures[round_num * (len(teams) // 2):(round_num + 1) * (len(teams) // 2)]:
            print(f"Adding reverse fixture: {fixture.away_team.name} vs {fixture.home_team.name} on {match_date.date}")
            fixtures.append(EuropeanCupFixture(
                fixture_number=next_fixture_number,
                home_team=fixture.away_team,
                away_team=fixture.home_team,
                group=group,
                european_cup_season=group.european_cup_season,
                round_stage="Group Stage",
                round_number=reverse_round_start + round_num + 1,
                date=match_date.date,
            ))
            next_fixture_number += 1

        match_date_index += 1

    # Update dates in `match_schedule` to assigned
    for match_date in match_schedule[:match_date_index]:
        match_date.is_euro_cup_day_assigned = True
        match_date.save()
        print(f"Updated match date {match_date.date} to assigned.")

    EuropeanCupFixture.objects.bulk_create(fixtures)
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

