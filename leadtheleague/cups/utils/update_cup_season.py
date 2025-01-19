from cups.models import SeasonCup, Cup
from cups.utils.generate_cup_fixtures import create_season_cup
from fixtures.models import CupFixture
from messaging.utils.category_messages_utils import create_cup_champion_message

def generate_cups_season(season):
    cups = Cup.objects.all()
    for cup in cups:
        if not SeasonCup.objects.filter(cup=cup, season=season).exists():
            create_season_cup(cup, season)

def set_season_cup_completed(season_cup):
    season_cup.is_completed = True
    season_cup.save()

def set_season_cup_winner(season_cup):
    final_fixture = CupFixture.objects.filter(season_cup=season_cup).order_by('-round_number').first()
    if not final_fixture or not final_fixture.winner:
        raise ValueError(f"Cannot determine winner for {season_cup}. Final match is missing or has no winner.")

    season_cup.champion_team = final_fixture.winner
    season_cup.save()
    create_cup_champion_message()

def update_winner(fixture):
    if fixture.home_goals > fixture.away_goals:
        fixture.winner = fixture.home_team
    elif fixture.away_goals > fixture.home_goals:
        fixture.winner = fixture.away_team
    else:
        fixture.winner = None
    fixture.is_finished = True
    fixture.save()

import logging

# Конфигуриране на logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Добавяне на StreamHandler за конзолата
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Добавяне на FileHandler за запис във файл
file_handler = logging.FileHandler('progressing_teams.log')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

def populate_progressing_team(season_cup):
    logger.info(f"Populating progressing teams for season cup: {season_cup.cup.name}, current stage: {season_cup.current_stage}")

    round_fixtures = CupFixture.objects.filter(season_cup=season_cup, round_stage=season_cup.current_stage)
    logger.info(f"Found {round_fixtures.count()} fixtures for current stage: {season_cup.current_stage}")

    unfinished_fixtures = round_fixtures.filter(is_finished=False)
    if unfinished_fixtures.exists():
        logger.info(f"Unfinished fixtures found: {[f.fixture_number for f in unfinished_fixtures]}")
        raise ValueError(f"Not all fixtures in {season_cup.current_stage} are finished.")

    progressing_teams = []
    eliminated_teams = []

    for fixture in round_fixtures:
        logger.info(f"Processing fixture {fixture.fixture_number}: {fixture.home_team.name} vs {fixture.away_team.name}")
        if fixture.winner:
            logger.info(f"Winner for fixture {fixture.fixture_number}: {fixture.winner.name}")
            progressing_teams.append(fixture.winner)

            if fixture.winner == fixture.home_team:
                eliminated_teams.append(fixture.away_team)
                logger.info(f"Eliminated team: {fixture.away_team.name}")
            else:
                eliminated_teams.append(fixture.home_team)
                logger.info(f"Eliminated team: {fixture.home_team.name}")
        else:
            logger.info(f"Fixture {fixture.fixture_number} has no winner set!")

    logger.info(f"Clearing old progressing teams for season cup: {season_cup.cup.name}")
    season_cup.progressing_teams.clear()

    logger.info(f"Setting new progressing teams: {[team.name for team in progressing_teams]}")
    season_cup.progressing_teams.set(progressing_teams)

    logger.info(f"Adding eliminated teams: {[team.name for team in eliminated_teams]}")
    season_cup.eliminated_teams.add(*eliminated_teams)

    logger.info(f"Saving updated season cup: {season_cup.cup.name}")
    season_cup.save()
    logger.info(f"Successfully populated progressing teams for season cup: {season_cup.cup.name}")


def set_champion(season_cup):
    if season_cup.current_stage.lower() == "final":
        final_fixture = CupFixture.objects.filter(season_cup=season_cup, round_stage='Final', is_finished=True).first()

        if final_fixture and final_fixture.winner:
            season_cup.champion_team = final_fixture.winner
            season_cup.is_completed = True
            season_cup.save()
        else:
            raise ValueError("The final match is not completed or has no winner.")
    else:
        raise ValueError("Current stage is not the final.")
