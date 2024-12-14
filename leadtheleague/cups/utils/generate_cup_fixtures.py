import random
from django.db import transaction
from django.db.models import Max
from django.db.utils import IntegrityError
from cups.models import SeasonCup
from cups.utils.get_cups_utils import determine_stage_by_teams_count
from fixtures.models import CupFixture
from fixtures.utils import create_cup_fixture
from teams.models import Team


def get_teams_for_cup(cup):
    teams_count = cup.teams_count
    nationality = cup.nationality

    active_teams = list(Team.objects.filter(is_active=True, nationality=nationality))
    inactive_teams = list(Team.objects.filter(is_active=False, nationality=nationality))

    if len(active_teams) < teams_count:
        random.shuffle(inactive_teams)
        additional_teams_needed = teams_count - len(active_teams)
        active_teams += inactive_teams[:additional_teams_needed]

    while len(active_teams) < teams_count:
        placeholder_team = Team.objects.create(
            name=f"Placeholder {len(active_teams) + 1}",
            is_active=False,
            nationality=nationality
        )
        active_teams.append(placeholder_team)

    random.shuffle(active_teams)
    return active_teams


def create_season_cup(cup, season):
    try:
        with transaction.atomic():
            season_cup, created = SeasonCup.objects.get_or_create(
                season=season,
                cup=cup,
                defaults={'current_stage': "Not Started"}
            )
            if created:
                print(f"SeasonCup създаден за купа '{cup.name}'.")

                teams = get_teams_for_cup(cup)
                if not teams:
                    print(f"Не са намерени отбори за купа '{cup.name}'.")
                    return None

                season_cup.participating_teams.set(teams)
                season_cup.save()
                print(f"Успешно свързани отбори за купа '{cup.name}'.")
            return season_cup
    except IntegrityError as e:
        print(f"Грешка при създаване на SeasonCup за купа '{cup.name}': {e}")
        return None


def generate_cup_fixtures(season_cup, cup):
    try:
        with transaction.atomic():
            if CupFixture.objects.filter(season_cup=season_cup).exists():
                print(f"Фикстури вече съществуват за купа '{cup.name}'.")
                return

            teams = list(season_cup.participating_teams.all())

            if len(teams) % 2 != 0:
                placeholder_team = Team.objects.create(
                    name="Bye Team",
                    is_active=False,
                    nationality=season_cup.cup.nationality
                )
                teams.append(placeholder_team)

            random.shuffle(teams)

            stage = determine_stage_by_teams_count(len(season_cup.progressing_teams.all()))
            season_cup.current_stage = stage
            season_cup.save()

            fixtures = []
            while len(teams) > 1:
                home_team = teams.pop(random.randint(0, len(teams) - 1))
                away_team = teams.pop(random.randint(0, len(teams) - 1))
                fixtures.append((home_team, away_team))

            max_fixture_number = CupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0

            for index, (home_team, away_team) in enumerate(fixtures, start=1):
                new_fixture_number = max_fixture_number + index

                create_cup_fixture(season_cup, new_fixture_number, home_team, away_team, season_cup.current_stage, 1,
                                   "18:00", None)

                print(f"Фикстура {home_team.name} vs {away_team.name} за купа '{cup.name}' създадена.")
    except IntegrityError as e:
        print(f"Error generating fixtures for SeasonCup: {season_cup.cup.name}: {e}")


# Generate next stage fixtures
def generate_next_round_fixtures(season_cup):
    progressing_teams = list(season_cup.progressing_teams.all())

    stage = determine_stage_by_teams_count(len(progressing_teams))
    season_cup.current_stage = stage
    season_cup.save()

    if len(progressing_teams) % 2 != 0:
        placeholder_team = Team.objects.create(
            name="Bye Team",
            is_active=False,
            nationality=season_cup.cup.nationality
        )
        progressing_teams.append(placeholder_team)

    random.shuffle(progressing_teams)

    fixtures = []
    while len(progressing_teams) > 1:
        home_team = progressing_teams.pop(random.randint(0, len(progressing_teams) - 1))
        away_team = progressing_teams.pop(random.randint(0, len(progressing_teams) - 1))
        fixtures.append((home_team, away_team))

    max_fixture_number = CupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0

    for index, (home_team, away_team) in enumerate(fixtures, start=1):
        new_fixture_number = max_fixture_number + index

        create_cup_fixture(
            season_cup=season_cup,
            fixture_number=new_fixture_number,
            home_team=home_team,
            away_team=away_team,
            round_stage=stage,
            round_number=season_cup.cupfixtures.count() // len(fixtures) + 1,
        )

        print(f"{home_team.name} vs {away_team.name} - '{season_cup.current_stage}'.")
