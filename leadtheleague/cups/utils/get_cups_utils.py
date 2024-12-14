from cups.models import Cup


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
