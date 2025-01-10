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

def populate_progressing_team(season_cup):
    round_fixtures = CupFixture.objects.filter(season_cup=season_cup, round_stage=season_cup.current_stage)
    print(f"Found {round_fixtures.count()} fixtures for current stage: {season_cup.current_stage}")

    if not round_fixtures.filter(is_finished=False).exists():
        progressing_teams = []
        eliminated_teams = []

        for fixture in round_fixtures:
            print(f"Processing fixture {fixture.fixture_number}: {fixture.home_team.name} vs {fixture.away_team.name}")
            if fixture.winner:
                print(f"Winner: {fixture.winner.name}")
                progressing_teams.append(fixture.winner)

                if fixture.winner == fixture.home_team:
                    eliminated_teams.append(fixture.away_team)
                else:
                    eliminated_teams.append(fixture.home_team)
            else:
                print(f"Fixture {fixture.fixture_number} has no winner!")

        print(f"Clearing old progressing teams.")
        season_cup.progressing_teams.clear()

        print(f"Setting new progressing teams: {[team.name for team in progressing_teams]}")
        season_cup.progressing_teams.set(progressing_teams)

        print(f"Adding eliminated teams: {[team.name for team in eliminated_teams]}")
        season_cup.eliminated_teams.add(*eliminated_teams)

        season_cup.save()
    else:
        raise ValueError(f"Not all fixtures in {season_cup.current_stage} are finished.")



def set_champion(season_cup):
    if season_cup.current_stage.lower() == "final":
        final_fixture = CupFixture.objects.filter(season_cup=season_cup, round_stage="Final", is_finished=True).first()

        if final_fixture and final_fixture.winner:
            season_cup.champion_team = final_fixture.winner
            season_cup.is_completed = True
            season_cup.save()
        else:
            raise ValueError("The final match is not completed or has no winner.")
    else:
        raise ValueError("Current stage is not the final.")