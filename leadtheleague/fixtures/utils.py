from django.db.models import Q
from fixtures.models import Fixture
from teams.models import Team
from datetime import timedelta
import random

def generate_fixtures(start_date, division, season, match_time):
    last_fixture = Fixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    teams = list(Team.objects.filter(division=division))
    random.shuffle(teams)

    # Ако броят на отборите е нечетен, добавяме "почивка"
    if len(teams) % 2 != 0:
        teams.append(None)  # None представлява "почивка"

    total_rounds = len(teams) - 1
    half_size = len(teams) // 2
    current_date = start_date
    round_number = 1

    schedule = []

    # Генерираме кръговете по метода на Бергер
    for r in range(total_rounds):
        round_pairs = []
        for i in range(half_size):
            home_team = teams[i]
            away_team = teams[-(i + 1)]

            if home_team is not None and away_team is not None:
                # Редуване на домакинства/гостувания
                if r % 2 == 0:
                    round_pairs.append((home_team, away_team))
                else:
                    round_pairs.append((away_team, home_team))

        schedule.append(round_pairs)
        # Завъртаме отборите за следващия кръг
        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    # Генерираме обратните мачове
    return_legs = []
    for fixture_round in schedule:
        return_legs.append([(away, home) for home, away in fixture_round])

    # Обединяваме кръговете в окончателния график
    full_schedule = schedule + return_legs

    # Създаваме фикстурите
    for fixture_round in full_schedule:
        for home_team, away_team in fixture_round:
            Fixture.objects.create(
                home_team=home_team,
                away_team=away_team,
                round_number=round_number,
                date=current_date,
                division=division,
                fixture_number=fixture_number,
                season=season,
                match_time=match_time
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

    return round_number


def shuffle_teams(teams):
    team_list = list(teams)
    random.shuffle(team_list)
    return team_list


def get_division_fixtures(division, round_number):
    if round_number is None:
        return Fixture.objects.filter(division_id=division.id).order_by('date')  # Връщаме всички мачове
    else:
        return Fixture.objects.filter(
            division_id=division.id,
            round_number=int(round_number)
        ).order_by('date')


def get_team_schedule(user_division, user_team):
    upcoming_matches = Fixture.objects.filter(
        Q(home_team=user_team) | Q(away_team=user_team),
        division=user_division,
        is_finished=False
    ).order_by('date', 'match_time')

    matches = []
    for match in upcoming_matches:
        if match.home_team == user_team:
            opponent = match.away_team
            location = 'H'
        else:
            opponent = match.home_team
            location = 'A'

        matches.append({
            'date': match.date.strftime("%Y-%m-%d"),
            'time': match.match_time.strftime("%H:%M"),
            'opponent': opponent.name,
            'location': location,
        })

    return matches


def update_fixtures(dummy_team, new_team):
    home_fixtures = Fixture.objects.filter(home_team=dummy_team)
    away_fixtures = Fixture.objects.filter(away_team=dummy_team)

    for fixture in home_fixtures:
        fixture.home_team = new_team
        fixture.save()

    for fixture in away_fixtures:
        fixture.away_team = new_team
        fixture.save()


def match_to_fixture(match):
    try:
        fixture = Fixture.objects.get(
            home_team=match.home_team,
            away_team=match.away_team,
            season=match.season,
            division=match.division,
            date=match.match_date  # Промяна на date -> match_date, за да съвпадне с полето в Match
        )

    except Fixture.DoesNotExist:
        return

    fixture.home_goals = match.home_goals
    fixture.away_goals = match.away_goals
    fixture.is_finished = True

    fixture.save()
