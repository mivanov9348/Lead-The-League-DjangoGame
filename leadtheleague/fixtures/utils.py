from fixtures.models import Fixture
from teams.models import Team
from datetime import timedelta
import random

def generate_fixtures(start_date, league, season, match_time):
    last_fixture = Fixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    teams = list(Team.objects.filter(league=league))
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
                league=league,
                fixture_number=fixture_number,
                season=season,
                match_time=match_time
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

    return round_number
