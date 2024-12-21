import random
from django.db import models, transaction
from europeancups.models import KnockoutTeam, KnockoutStage
from fixtures.models import EuropeanCupFixture
from game.models import MatchSchedule


def get_knockout_stage_name(team_count):
    if team_count == 16:
        return "Round of 16"
    elif team_count == 8:
        return "Quarter-Final"
    elif team_count == 4:
        return "Semi-Final"
    elif team_count == 2:
        return "Final"
    else:
        return f"Knockout Stage ({team_count} Teams)"


def create_knockout_stage(european_cup_season, stage_order, stage_name, teams_per_match=2, is_final=False):
    knockout_stage, created = KnockoutStage.objects.get_or_create(
        european_cup_season=european_cup_season,
        stage_order=stage_order,
        defaults={
            'stage_name': stage_name,
            'teams_per_match': teams_per_match,
            'is_final': is_final,
        }
    )
    return knockout_stage


def create_knockout_team(team):
    return KnockoutTeam.objects.create(
        team=team
    )


def update_knockout_teams(knockout_stage, advancing_teams):
    KnockoutTeam.objects.filter(knockout_stage=knockout_stage).delete()

    for team in advancing_teams:
        KnockoutTeam.objects.create(knockout_stage=knockout_stage, team=team)


def generate_euro_cup_knockout(european_cup_season, match_date):
    current_stage = european_cup_season.knockout_stages.order_by('-stage_order').first()
    next_stage_order = (current_stage.stage_order + 1) if current_stage else 1

    teams = list(KnockoutTeam.objects.filter(knockout_stage=current_stage).values_list('team', flat=True))
    if len(teams) % 2 != 0:
        raise ValueError("Odd number of teams in the knockout stage!")

    stage_name = get_knockout_stage_name(len(teams))

    knockout_stage = KnockoutStage.objects.create(
        european_cup_season=european_cup_season,
        stage_order=next_stage_order,
        stage_name=stage_name,
        teams_per_match=2,
        is_final=(len(teams) == 2)
    )

    random.shuffle(teams)

    max_fixture_number = (
            EuropeanCupFixture.objects.aggregate(
                max_number=models.Max('fixture_number')
            )['max_number'] or 0
    )

    fixtures = []
    for i in range(0, len(teams), 2):
        home_team = teams[i]
        away_team = teams[i + 1]

        fixture = EuropeanCupFixture.objects.create(
            european_cup_season=european_cup_season,
            knockout_stage=knockout_stage,
            home_team_id=home_team,
            away_team_id=away_team,
            date=match_date,
            round_stage=knockout_stage.stage_name,
            season=european_cup_season.season,
            round_number=knockout_stage.stage_order,
            fixture_number=max_fixture_number + 1
        )
        max_fixture_number += 1
        fixtures.append(fixture)

    return fixtures


def simulate_euro_knockout_round(european_cup_season, knockout_stage):
    fixtures = EuropeanCupFixture.objects.filter(
        european_cup_season=european_cup_season,
        knockout_stage=knockout_stage,
        is_finished=False
    )

    if not fixtures.exists():
        raise ValueError(f"No fixtures to simulate for the stage {knockout_stage.stage_name}.")

    match_date = fixtures.first().date

    advancing_teams = []

    with transaction.atomic():
        for fixture in fixtures:
            home_goals = random.randint(0, 5)
            away_goals = random.randint(0, 5)

            fixture.home_goals = home_goals
            fixture.away_goals = away_goals
            fixture.is_finished = True

            if home_goals > away_goals:
                winner = fixture.home_team
            elif away_goals > home_goals:
                winner = fixture.away_team
            else:
                winner = fixture.home_team if random.randint(0, 1) == 0 else fixture.away_team

            fixture.winner = winner
            fixture.save()
            advancing_teams.append(winner)

        knockout_stage.is_played = True
        knockout_stage.save()

        match_schedule = MatchSchedule.objects.filter(
            date=match_date,
            season=european_cup_season.season,
            event_type='euro'
        ).first()

        if match_schedule:
            match_schedule.is_played = True
            match_schedule.save()

        update_knockout_teams(knockout_stage, advancing_teams)

    return advancing_teams

