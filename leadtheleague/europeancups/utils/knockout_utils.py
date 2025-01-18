import random
from webbrowser import Konqueror

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from europeancups.models import KnockoutTeam, KnockoutStage
from fixtures.models import EuropeanCupFixture
from game.models import MatchSchedule
from match.models import Match
from match.utils.match.generator import generate_matches_from_fixtures


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


def finish_current_knockout_stage(current_stage):
    knockout_stage = KnockoutStage.objects.filter(stage_order=current_stage.stage_order).first()

    if not knockout_stage:
        raise ValueError(f"Knockout stage with stage_order {current_stage.stage_order} does not exist.")

    knockout_stage.is_played = True
    knockout_stage.save()


def create_knockout_team(team):
    return KnockoutTeam.objects.create(
        team=team
    )


def update_knockout_teams(match):
    winner_team = match.home_team if match.home_goals > match.away_goals else match.away_team
    loser_team = match.away_team if match.home_goals > match.away_goals else match.home_team

    KnockoutTeam.objects.filter(team=loser_team, knockout_stage__european_cup_season=match.european_cup_season).update(
        is_eliminated=True
    )

def generate_euro_cup_knockout(european_cup_season, match_date):
    current_stage = european_cup_season.knockout_stages.order_by('-stage_order').first()

    if current_stage:
        fixtures = current_stage.fixtures.all()
        for match in fixtures:
            if match.is_finished:
                update_knockout_teams(match)

    advancing_teams = list(KnockoutTeam.objects.filter(
        knockout_stage=current_stage,
        is_eliminated=False
    ).values_list('team', flat=True))

    if len(advancing_teams) % 2 != 0:
        raise ValueError("Нечетен брой отбори се класират за следващия етап!")

    next_stage_order = (current_stage.stage_order + 1) if current_stage else 1
    stage_name = get_knockout_stage_name(len(advancing_teams))

    knockout_stage = KnockoutStage.objects.create(
        european_cup_season=european_cup_season,
        stage_order=next_stage_order,
        stage_name=stage_name,
        teams_per_match=2,
        is_final=(len(advancing_teams) == 2)
    )

    max_fixture_number = (
        EuropeanCupFixture.objects.aggregate(max_number=models.Max('fixture_number'))['max_number'] or 0
    )

    random.shuffle(advancing_teams)
    fixtures = []
    for i in range(0, len(advancing_teams), 2):
        home_team = advancing_teams[i]
        away_team = advancing_teams[i + 1]

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

    for team_id in advancing_teams:
        KnockoutTeam.objects.create(knockout_stage=knockout_stage, team_id=team_id)

    generate_matches_from_fixtures(fixtures, 'euro_cup', european_cup_season.season)

    return fixtures

