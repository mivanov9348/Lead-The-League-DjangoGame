from cups.models import Cup, SeasonCup
from europeancups.models import EuropeanCupTeam


def get_all_cups():
    cups = Cup.objects.all()
    return cups


def determine_stage_by_teams_count(teams_count):
    stages = {
        2: "Final",
        4: "Semi-Final",
        8: "Quarter-Final",
        16: "Round of 16",
        32: "Round of 32",
        64: "Round of 64",
    }

    return stages.get(teams_count, "Unknown Stage")


def promote_cup_champions_to_europe(new_season, new_european_cup_season):
    previous_season_cups = SeasonCup.objects.filter(season__year=new_season.year - 1, is_completed=True)
    cup_champions = []

    for cup in previous_season_cups:
        if cup.champion_team:
            cup_champions.append(cup.champion_team)
            EuropeanCupTeam.objects.create(
                team=cup.champion_team,
                european_cup_season=new_european_cup_season
            )
            print(f"Added Cup Champion {cup.champion_team.name} to European Cups.")

    return cup_champions
