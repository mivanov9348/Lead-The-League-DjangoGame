import random
from django.db import transaction
from django.db.models import Max
from europeancups.models import EuropeanCupTeam, GroupTeam, Group, EuropeanCupSeason
from europeancups.utils.knockout_utils import create_knockout_team, create_knockout_stage
from fixtures.models import EuropeanCupFixture
from game.models import MatchSchedule


def create_groups_for_season(season):
    european_cup_season = EuropeanCupSeason.objects.get(season=season)
    if not european_cup_season:
        raise ValueError(f"No European Cup Season found for season {season}.")

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
            GroupTeam.objects.bulk_create([
                GroupTeam(group=group, team=european_cup_team.team)
                for european_cup_team in group_teams
            ])

    return f"Groups created successfully for {european_cup_season}!"

def generate_group_fixtures(season):
    european_cup_season = EuropeanCupSeason.objects.get(season=season)
    if not european_cup_season:
        raise ValueError(f"No European Cup Season found for season {season}.")

    groups = Group.objects.filter(european_cup_season=european_cup_season)
    if not groups.exists():
        raise ValueError("No groups found for the specified season.")

    def generate_fixtures_for_group(group, shared_dates):
        group_teams = list(GroupTeam.objects.filter(group=group))
        teams = [team.team for team in group_teams]

        if len(teams) < 2:
            raise ValueError("Group must have at least two teams to generate fixtures.")

        if len(teams) % 2 != 0:
            teams.append(None)  # Add a bye if odd number of teams

        num_rounds = len(teams) - 1
        total_rounds = 2 * num_rounds

        if len(shared_dates) < total_rounds:
            raise ValueError(f"Not enough match dates. Needed: {total_rounds}, available: {len(shared_dates)}.")

        max_fixture_number = EuropeanCupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0
        next_fixture_number = max_fixture_number + 1
        fixtures = []

        def rotate_teams(teams):
            return [teams[0]] + [teams[-1]] + teams[1:-1]

        match_date_index = 0

        # First half fixtures
        for round_num in range(num_rounds):
            round_matches = [
                (teams[i], teams[-(i + 1)]) for i in range(len(teams) // 2) if teams[i] and teams[-(i + 1)]
            ]
            match_date = shared_dates[match_date_index]

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

        # Second half fixtures (reversed)
        for round_num in range(num_rounds):
            round_matches = [
                (fixture.away_team, fixture.home_team)
                for fixture in fixtures[round_num * (len(teams) // 2):(round_num + 1) * (len(teams) // 2)]
            ]
            match_date = shared_dates[match_date_index]

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

        EuropeanCupFixture.objects.bulk_create(fixtures)

    # Fetch shared dates once for the entire process
    shared_dates = list(
        MatchSchedule.objects.filter(
            event_type='euro',
            is_euro_cup_day_assigned=False
        ).order_by('date')
    )

    for group in groups:
        generate_fixtures_for_group(group, shared_dates)

    # Mark shared dates as assigned
    for match_date in shared_dates:
        match_date.is_euro_cup_day_assigned = True
        match_date.save()

    return f"Successfully generated fixtures for all groups in season {season}!"


def simulate_matchday_matches(euro_cup_match_day):
    fixtures = EuropeanCupFixture.objects.filter(
        date=euro_cup_match_day,
        group__isnull=False,
        is_finished=False
    )

    for fixture in fixtures:
        home_team = fixture.home_team
        away_team = fixture.away_team

        home_goals = random.randint(0, 5)
        away_goals = random.randint(0, 5)

        fixture.home_goals = home_goals
        fixture.away_goals = away_goals
        fixture.is_finished = True

        if home_goals > away_goals:
            fixture.winner = home_team
        elif away_goals > home_goals:
            fixture.winner = away_team
        else:
            fixture.winner = None

        fixture.save()

    match_day = MatchSchedule.objects.get(date=euro_cup_match_day, event_type='euro')
    match_day.is_played = True
    match_day.save()


def update_euro_cup_standings(match_day):
    """Updates group standings based on fixtures played on the specified match day."""
    finished_fixtures = EuropeanCupFixture.objects.filter(
        is_finished=True,
        group__isnull=False,
        date=match_day
    )

    for fixture in finished_fixtures:
        home_team = fixture.home_team
        away_team = fixture.away_team

        home_group_team = GroupTeam.objects.get(group=fixture.group, team=home_team)
        away_group_team = GroupTeam.objects.get(group=fixture.group, team=away_team)

        home_goals = fixture.home_goals
        away_goals = fixture.away_goals

        # Update statistics for home team
        home_group_team.matches += 1
        home_group_team.goals_for += home_goals
        home_group_team.goals_against += away_goals
        home_group_team.goals_difference = home_group_team.goals_for - home_group_team.goals_against

        # Update statistics for away team
        away_group_team.matches += 1
        away_group_team.goals_for += away_goals
        away_group_team.goals_against += home_goals
        away_group_team.goals_difference = away_group_team.goals_for - away_group_team.goals_against

        if fixture.winner == home_team:
            home_group_team.wins += 1
            home_group_team.points += 3
            away_group_team.loses += 1
        elif fixture.winner == away_team:
            away_group_team.wins += 1
            away_group_team.points += 3
            home_group_team.loses += 1
        else:
            home_group_team.draws += 1
            home_group_team.points += 1
            away_group_team.draws += 1
            away_group_team.points += 1

        home_group_team.save()
        away_group_team.save()


def advance_teams_from_groups(european_cup_season):
    teams_qualify_from_group = european_cup_season.total_teams_qualify_from_group
    advancing_teams = []
    eliminated_teams = []

    with transaction.atomic():
        for group in Group.objects.filter(european_cup_season=european_cup_season):
            group_teams = GroupTeam.objects.filter(group=group).order_by(
                '-points', '-goals_difference', '-goals_for'
            )

            # Отбори, които продължават
            qualified_teams = group_teams[:teams_qualify_from_group]
            for group_team in qualified_teams:
                european_cup_team = EuropeanCupTeam.objects.get(
                    team=group_team.team,
                    european_cup_season=european_cup_season
                )
                european_cup_team.is_eliminated = False
                european_cup_team.save()
                advancing_teams.append(group_team.team.name)

                # Създаваме KnockoutTeam
                create_knockout_team(group_team.team)

            # Отбори, които отпадат
            for group_team in group_teams[teams_qualify_from_group:]:
                european_cup_team = EuropeanCupTeam.objects.get(
                    team=group_team.team,
                    european_cup_season=european_cup_season
                )
                european_cup_team.is_eliminated = True
                european_cup_team.save()
                eliminated_teams.append(group_team.team.name)

    return advancing_teams, eliminated_teams
