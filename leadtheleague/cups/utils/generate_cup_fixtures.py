import random
from django.db import transaction
from django.db.models import Max
from django.db.utils import IntegrityError
from cups.models import SeasonCup
from fixtures.models import CupFixture
from game.utils.get_season_stats_utils import get_current_season
from teams.models import Team
import logging

logging.basicConfig(
    filename='cup_generation.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_teams_for_cup(cup):
    logging.info(f"Getting teams for cup: {cup.name}")
    teams_count = cup.teams_count
    nationality = cup.nationality

    active_teams = list(Team.objects.filter(is_active=True, nationality=nationality))
    inactive_teams = list(Team.objects.filter(is_active=False, nationality=nationality))
    logging.debug(f"Active teams: {len(active_teams)}, Inactive teams: {len(inactive_teams)}")

    if len(active_teams) < teams_count:
        random.shuffle(inactive_teams)
        required_inactive = teams_count - len(active_teams)
        active_teams += inactive_teams[:required_inactive]

    while len(active_teams) < teams_count:
        placeholder_team = Team(name=f"Placeholder {len(active_teams) + 1}", is_active=False, nationality=nationality)
        placeholder_team.save()
        logging.warning(f"Adding placeholder team: {placeholder_team.name}")
        active_teams.append(placeholder_team)

    random.shuffle(active_teams)
    logging.info(f"Total teams for cup {cup.name}: {len(active_teams)}")
    return active_teams

def create_season_cup(cup, season):
    logging.info(f"Creating SeasonCup for cup: {cup.name} in season {season.year}")
    try:
        with transaction.atomic():
            season_cup, created = SeasonCup.objects.get_or_create(
                season=season,
                cup=cup,
                defaults={'current_stage': "Not Started"}
            )

            if created:
                teams = get_teams_for_cup(cup)
                if not teams:
                    logging.error(f"Not enough teams for cup: {cup.name}")
                    return None

                season_cup.participating_teams.set(teams)
                season_cup.save()
                logging.info(f"SeasonCup created for cup: {cup.name}")

            return season_cup
    except IntegrityError as e:
        logging.error(f"Error creating SeasonCup for cup {cup.name}: {e}")
        return None

def generate_fixtures_for_season_cup(season_cup):
    logging.info(f"Generating fixtures for SeasonCup: {season_cup.cup.name}")
    try:
        with transaction.atomic():
            if CupFixture.objects.filter(season_cup=season_cup).exists():
                logging.warning(f"Fixtures already exist for SeasonCup: {season_cup.cup.name}")
                return

            teams = list(season_cup.participating_teams.all())
            logging.debug(f"Participating teams: {[team.name for team in teams]}")

            if len(teams) % 2 != 0:
                placeholder_team = Team(name="Bye Team", is_active=False, nationality=season_cup.cup.nationality)
                placeholder_team.save()
                teams.append(placeholder_team)
                logging.warning(f"Odd number of teams, added placeholder team: {placeholder_team.name}")

            fixtures = []
            for i in range(0, len(teams), 2):
                if i + 1 < len(teams):
                    fixtures.append((teams[i], teams[i + 1]))

            max_fixture_number = (
                CupFixture.objects.filter(season_cup=season_cup)
                .aggregate(Max('fixture_number'))['fixture_number__max'] or 0
            )

            for index, (home_team, away_team) in enumerate(fixtures, start=1):
                CupFixture.objects.create(
                    fixture_number=max_fixture_number + index,
                    home_team=home_team,
                    away_team=away_team,
                    round_number=1,
                    date=None,
                    match_time="18:00",
                    season=season_cup.season,
                    season_cup=season_cup,
                    round_stage="Round of 32",
                )
                logging.info(f"Fixture created: {home_team.name} vs {away_team.name}")
    except IntegrityError as e:
        logging.error(f"Error generating fixtures for SeasonCup: {season_cup.cup.name}: {e}")

def generate_season_cup_and_fixtures(cup):
    logging.info(f"Starting generation for cup: {cup.name}")
    current_season = get_current_season()
    season_cup = create_season_cup(cup, current_season)

    if season_cup:
        generate_fixtures_for_season_cup(season_cup)
    else:
        logging.warning(f"SeasonCup not created for cup: {cup.name}")
