import random
from django.db import transaction
from django.db.models import Max
from django.db.utils import IntegrityError
from cups.models import SeasonCup
from cups.utils.get_cups_utils import determine_stage_by_teams_count
from fixtures.models import CupFixture
from game.models import MatchSchedule
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

def get_first_available_cup_schedule(season):
    return MatchSchedule.objects.filter(
        season=season,
        event_type='cup',
        is_cup_day_assigned=False
    ).order_by('date').first()

def process_all_season_cups(season):
    season_cups = SeasonCup.objects.filter(season=season)
    first_available_schedule = get_first_available_cup_schedule(season)

    for season_cup in season_cups:

        if not first_available_schedule:
            raise ValueError(f"Няма наличен график за мачове в сезон {season} за купа.")

        generate_cup_fixtures(season_cup, first_available_schedule)

def generate_cup_fixtures(season_cup, first_available_schedule):
    try:
        with transaction.atomic():
            if CupFixture.objects.filter(season_cup=season_cup).exists():
                return  # Мачовете за този сезон вече са създадени

            teams = list(season_cup.participating_teams.all())

            # Добавяме "бай" отбор, ако броят на отборите е нечетен
            if len(teams) % 2 != 0:
                placeholder_team, _ = Team.objects.get_or_create(
                    name="Bye Team",
                    is_active=False,
                    nationality=season_cup.cup.nationality
                )
                teams.append(placeholder_team)

            random.shuffle(teams)

            # Създаваме двойки за срещи
            fixtures = []
            while len(teams) > 1:
                home_team = teams.pop(random.randint(0, len(teams) - 1))
                away_team = teams.pop(random.randint(0, len(teams) - 1))
                fixtures.append((home_team, away_team))

            max_fixture_number = CupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0
            bulk_create_list = []

            # Създаваме обекти за всички срещи
            for index, (home_team, away_team) in enumerate(fixtures):
                new_fixture_number = max_fixture_number + index + 1
                bulk_create_list.append(CupFixture(
                    fixture_number=new_fixture_number,
                    home_team=home_team,
                    away_team=away_team,
                    round_number=1,
                    date=first_available_schedule.date,
                    match_time=first_available_schedule.season.match_time,
                    season=season_cup.season,
                    season_cup=season_cup,
                    round_stage="Round 1"
                ))

            first_available_schedule.is_cup_day_assigned = True
            first_available_schedule.save()

            # Вмъкваме мачовете в базата данни
            CupFixture.objects.bulk_create(bulk_create_list)

        season_cup.current_stage = 'Round 1'
        season_cup.save()

    except IntegrityError as e:
        raise ValueError(f"Грешка при генериране на мачове за Cup: {e}")
    except Exception as e:
        raise ValueError(f"Неочаквана грешка: {e}")


def generate_next_round_fixtures(season_cup, shared_match_date):
    try:
        with transaction.atomic():
            progressing_teams = list(season_cup.progressing_teams.all())
            if len(progressing_teams) < 2:
                raise ValueError(f"Not enough teams to generate the next round for {season_cup.cup.name}.")

            if len(progressing_teams) % 2 != 0:
                placeholder_team = Team.objects.create(
                    name="Bye Team",
                    is_active=False,
                    nationality=season_cup.cup.nationality
                )
                progressing_teams.append(placeholder_team)

            random.shuffle(progressing_teams)
            stage = determine_stage_by_teams_count(len(progressing_teams))
            season_cup.current_stage = stage
            season_cup.save()

            fixtures = []
            while len(progressing_teams) > 1:
                home_team = progressing_teams.pop(random.randint(0, len(progressing_teams) - 1))
                away_team = progressing_teams.pop(random.randint(0, len(progressing_teams) - 1))
                fixtures.append((home_team, away_team))

            max_fixture_number = CupFixture.objects.aggregate(Max('fixture_number'))['fixture_number__max'] or 0

            bulk_create_list = []
            for index, (home_team, away_team) in enumerate(fixtures):
                new_fixture_number = max_fixture_number + index + 1

                cup_fixture = CupFixture(
                    fixture_number=new_fixture_number,
                    home_team=home_team,
                    away_team=away_team,
                    round_number=(season_cup.cup_fixtures.aggregate(Max('round_number'))['round_number__max'] or 0) + 1,
                    date=shared_match_date.date,
                    match_time=shared_match_date.season.match_time,
                    season=season_cup.season,
                    season_cup=season_cup,
                    round_stage=stage,
                )
                bulk_create_list.append(cup_fixture)

            CupFixture.objects.bulk_create(bulk_create_list)

        season_cup.current_stage = stage
        season_cup.save()
    except IntegrityError as e:
        raise ValueError(f"Error generating next round fixtures for {season_cup.cup.name}: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {e}")
