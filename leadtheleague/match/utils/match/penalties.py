from match.models import MatchPenalties


def generate_match_penalties(match):
    if not hasattr(match, 'penalties'):
        match_penalties, created = MatchPenalties.objects.get_or_create(
            match=match,
            defaults={
                "home_score": 0,
                "away_score": 0,
                "is_completed": False,
                "current_initiative": match.home_team,
            }
        )
        if created:
            print(f"Initialized penalties for match {match.id} with home team initiative.")
        else:
            print(f"Penalties already exist for match {match.id}.")
        return match_penalties


def process_penalties(match):
    print("Initializing penalty shootout...")
    # Initialize the penalty shootout
    match_penalties = generate_match_penalties(match)
    print(match_penalties)
    print("Setting up team data...")

    # Initialize tracking for each team
    team_data = {
        match.home_team: {
            "taken_penalty_players": [],
            "execution_order": get_starting_lineup(match.home_team)
        },
        match.away_team: {
            "taken_penalty_players": [],
            "execution_order": get_starting_lineup(match.away_team)
        }
    }

    print("Determining team with initiative...")
    # Determine which team starts the penalty shootout
    match_penalties.current_initiative = match.home_team
    team_with_initiative = match_penalties.current_initiative

    # Process first 5 penalties per team
    print("Processing first 5 penalties per team...")
    process_initial_penalties(match, match_penalties, team_data)

    if not match_penalties.is_completed:
        print("Processing sudden death penalties...")
        process_sudden_death(match, match_penalties, team_data)


def process_initial_penalties(match, match_penalties, team_data):
    home_team = match.home_team
    away_team = match.away_team

    for round_number in range(5):
        if match_penalties.is_completed:
            print("Penalty shootout completed during initial round.")
            break

        print(f"Round {round_number + 1}: {home_team.name} is taking a penalty.")
        handle_penalty_attempt(match, match_penalties, team_data, home_team)

        if check_penalties_completion(match_penalties):
            print("Penalty shootout completed! Home team wins!")
            break

        print(f"Round {round_number + 1}: {away_team.name} is taking a penalty.")
        handle_penalty_attempt(match, match_penalties, team_data, away_team)

        if check_penalties_completion(match_penalties):
            print("Penalty shootout completed! Away team wins!")
            break


def process_sudden_death(match, match_penalties, team_data):
    home_team = match.home_team
    away_team = match.away_team

    while not match_penalties.is_completed:
        # Home team attempts
        print(f"Sudden death - {home_team.name} is taking a penalty.")
        handle_penalty_attempt(match, match_penalties, team_data, home_team)

        # Away team attempts
        print(f"Sudden death - {away_team.name} is taking a penalty.")
        handle_penalty_attempt(match, match_penalties, team_data, away_team)

        if check_sudden_death_completion(match_penalties):
            print("Sudden death completed! Away team wins!")
            break


def handle_penalty_attempt(match, match_penalties, team_data, team_with_initiative):
    with transaction.atomic():
        current_team = team_with_initiative
        current_data = team_data[current_team]

        print(f"Checking rotation violations for team {current_team.name}...")
        if check_rotation_violations(current_team, current_data["taken_penalty_players"]):
            print(f"Rotation complete for team {current_team.name}. Restarting lineup.")
            current_data["execution_order"] = get_starting_lineup(current_team)
            current_data["taken_penalty_players"] = []

        if not current_data["execution_order"]:
            print(f"Execution order for team {current_team.name} is empty. Restarting lineup.")
            current_data["execution_order"] = get_starting_lineup(current_team)
            current_data["taken_penalty_players"] = []

        print(f"Current execution order for team {current_team.name}: {current_data['execution_order']}")
        print(f"Players who took penalties: {current_data['taken_penalty_players']}")

        penalty_taker_id = current_data["execution_order"].pop(0)
        penalty_taker = get_penalty_taker(current_team, current_data["taken_penalty_players"])

        print(f"Player {penalty_taker.name} from team {current_team.name} is taking the penalty.")
        event = get_penalty_match_event()
        success = calculate_event_success_rate(event, penalty_taker)
        event_result = get_event_result(event, success)
        print(f'Event result: {event_result.event_result}')
        is_goal = calculate_penalty_success(event_result.event_result)

        template = get_event_template(event_result)
        formatted_template = fill_template_with_player(template, penalty_taker)

        print(f"Penalty Result: {formatted_template}")
        log_penalty_event(match, formatted_template, penalty_taker, success)

        print("Updating penalty shootout score...")
        update_penalty_score(match_penalties, is_goal, current_team)

        print("Saving penalty attempt...")
        attempt_order = len(match_penalties.attempts.all()) + 1

        PenaltyAttempt.objects.create(
            match_penalty=match_penalties,
            player=penalty_taker,
            is_goal=is_goal,
            attempt_order=attempt_order,
            team=current_team
        )

        print(f"Tracking player {penalty_taker.name} who took the penalty...")
        current_data["taken_penalty_players"].append(penalty_taker.id)
