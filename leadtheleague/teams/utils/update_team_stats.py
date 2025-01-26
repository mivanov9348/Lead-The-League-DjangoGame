def update_reputation_after_match(team, attendance, result):
    if result == 'win':
        team.reputation += attendance // 100
    elif result == 'draw':
        team.reputation += attendance // 200
    else:  # Loss
        team.reputation += attendance // 300

    team.reputation = max(1, min(10000, team.reputation))
    team.save()

