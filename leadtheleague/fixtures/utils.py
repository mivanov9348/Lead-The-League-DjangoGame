from fixtures.models import Fixture
from leagues.models import DivisionTeam
from teams.models import Team
from datetime import timedelta
import random


def generate_fixtures(start_date, division):
    last_fixture = Fixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    teams_in_division = DivisionTeam.objects.filter(division_id=division.id).values_list('team_id', flat=True)
    teams = Team.objects.filter(id__in=teams_in_division)

    teams = shuffle_teams(teams)
    total_rounds = len(teams) - 1

    current_date = start_date
    round_number = 1

    while round_number <= total_rounds:
        for i in range(len(teams) // 2):
            home_team = teams[i]
            away_team = teams[-(i + 1)]
            Fixture.objects.create(
                home_team=home_team,
                away_team=away_team,
                round_number=round_number,
                date=current_date,
                division=division,
                fixture_number=fixture_number
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    for reverse_round in range(1, total_rounds + 1):
        for i in range(len(teams) // 2):
            away_team = teams[i]
            home_team = teams[-(i + 1)]
            Fixture.objects.create(
                home_team=home_team,
                away_team=away_team,
                round_number=round_number,
                date=current_date,
                division=division,
                fixture_number=fixture_number
            )
            fixture_number += 1

        round_number += 1
        current_date += timedelta(days=1)

        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    return round_number

def shuffle_teams(teams):
    team_list = list(teams)
    random.shuffle(team_list)
    return team_list
