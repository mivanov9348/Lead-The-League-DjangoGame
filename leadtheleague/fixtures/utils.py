from fixtures.models import Fixture
from teams.models import Team
from datetime import timedelta
import random

def generate_fixtures(start_date, division, season, match_time):
    last_fixture = Fixture.objects.order_by('-fixture_number').first()
    fixture_number = last_fixture.fixture_number + 1 if last_fixture else 1

    teams = Team.objects.filter(division=division)

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
                fixture_number=fixture_number,
                season=season,
                match_time=match_time
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
                fixture_number=fixture_number,
                season=season,
                match_time=match_time
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

def get_division_fixtures(division, round_number):
    if round_number is None:
        return Fixture.objects.filter(division_id=division.id).order_by('date')  # Връщаме всички мачове
    else:
        return Fixture.objects.filter(
            division_id=division.id,
            round_number=int(round_number)  # Конвертиране на round_number в int
        ).order_by('date')

def get_team_schedule(user_division, user_team):
    upcoming_matches = Fixture.objects.filter(
        division=user_division,
        is_finished=False
    ).order_by('date', 'match_time')[:5]

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
