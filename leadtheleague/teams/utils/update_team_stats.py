from teams.models import TeamPlayer


def update_reputation_after_match(team, attendance, result):
    if result == 'win':
        team.reputation += attendance // 100
    elif result == 'draw':
        team.reputation += attendance // 200
    else:  # Loss
        team.reputation += attendance // 300

    team.reputation = max(1, min(10000, team.reputation))
    team.save()


def get_available_shirt_number(team):
    used_numbers = TeamPlayer.objects.filter(team=team).values_list('shirt_number', flat=True)

    min_number = 1
    while min_number in used_numbers:
        min_number += 1

    return min_number
