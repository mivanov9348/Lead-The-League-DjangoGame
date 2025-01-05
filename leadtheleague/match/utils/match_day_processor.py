from cups.models import SeasonCup
from cups.utils.generate_cup_fixtures import generate_next_round_fixtures
from cups.utils.update_cup_season import populate_progressing_team
from europeancups.utils.euro_cup_season_utils import get_current_european_cup_season, get_current_knockout_stage_order, \
    are_knockout_matches_finished
from europeancups.utils.group_stage_utils import update_euro_cup_standings, are_group_stage_matches_finished, \
    advance_teams_from_groups
from europeancups.utils.knockout_utils import generate_euro_cup_knockout
from fixtures.utils import transfer_match_to_fixture, get_fixtures_by_date
from game.models import MatchSchedule
from leagues.utils import update_standings_from_fixtures
from match.models import Match, PenaltyAttempt
from match.utils.generate_match_stats_utils import generate_players_match_stats, generate_match_penalties
from match.utils.lineup_utils import get_starting_lineup
from match.utils.match_helpers import update_match_minute, get_match_team_initiative, choose_event_random_player, \
    get_random_match_event, log_match_event, finalize_match, \
    check_initiative, \
    update_match_score, handle_card_event, update_player_stats_from_template, fill_template_with_player, \
    get_event_result, get_event_template, get_event_weights, calculate_event_success_rate
from match.utils.match_penalties_helpers import get_penalty_taker, update_penalty_score, check_penalties_completion, \
    update_penalty_initiative, log_penalty_event, check_rotation_violations, get_penalty_match_event, \
    calculate_penalty_success
from messaging.utils.notifications_utils import create_match_notifications
from players.utils.get_player_stats_utils import get_player_attributes
from players.utils.player_analytics_utils import update_season_analytics
from players.utils.update_player_stats_utils import update_season_statistics_for_match
from teams.utils.lineup_utils import ensure_team_tactics
from django.db import transaction

def match_day_processor(date=None):
    today = date if date else date.today()
    match_date = MatchSchedule.objects.filter(date=today).first()

    if not match_date:
        print(f"No schedule found for today ({today}).")
        return

    print(f"Processing match day for {today}: {match_date.event_type}")

    try:
        with transaction.atomic():
            if match_date.event_type == 'league':
                process_league_day(match_date)
            elif match_date.event_type == 'cup':
                process_cup_day(match_date)
            elif match_date.event_type == 'euro':
                process_euro_day(match_date)
            else:
                print(f"Unknown event type: {match_date.event_type}")
                return

            match_date.is_played = True
            match_date.save()
            create_match_notifications(match_date)
            update_season_analytics()

    except Exception as e:
        print(f"Error processing match day: {e}")
        return

    print(f"Match day processing completed for {today}.")


def process_league_day(match_date):
    print("Processing league matches...")
    matches = Match.objects.filter(
        season=match_date.season,
        league_season__isnull=False,
        match_date=match_date.date,
        is_played=False
    )

    for match in matches:
        process_match(match)
        update_season_statistics_for_match(match)
        finalize_match(match)

    fixtures = get_fixtures_by_date(match_date.date)
    update_standings_from_fixtures(fixtures)

def process_cup_day(match_date):
    print("Processing cup matches...")
    matches = Match.objects.filter(
        season=match_date.season,
        season_cup__isnull=False,
        match_date=match_date.date,
        is_played=False
    )

    for match in matches:
        process_match(match)
        if match.home_goals == match.away_goals:
            process_penalties(match)
        else:
            update_season_statistics_for_match(match)

        finalize_match(match)

    next_available_date = MatchSchedule.objects.filter(
        season=match_date.season,
        event_type='cup',
        is_cup_day_assigned=False,
        date__gt=match_date.date
    ).order_by('date').first()

    if not next_available_date:
        print("No available date for the next cup round.")
        return

    season_cups = SeasonCup.objects.filter(season=match_date.season)
    for season_cup in season_cups:
        try:
            print(f"Processing {season_cup.cup.name} ({season_cup.season.year})...")
            populate_progressing_team(season_cup)
            generate_next_round_fixtures(season_cup, next_available_date)

            next_available_date.is_cup_day_assigned = True
            next_available_date.save()
        except Exception as e:
            print(f"Error processing {season_cup.cup.name}: {e}")


def process_euro_day(match_date):
    print("Starting processing of European cup matches...")

    current_euro_season = get_current_european_cup_season()
    print(f"Current European Cup Season: {current_euro_season}")

    matches = Match.objects.filter(
        season=match_date.season,
        european_cup_season__isnull=False,
        match_date=match_date.date,
        is_played=False
    )
    print(f"Found {len(matches)} matches for date {match_date.date}.")

    for match in matches:
        print(f"Processing match {match.id} between {match.home_team.name} and {match.away_team.name}...")
        process_match(match)
        print(f"Match processed. Score: {match.home_goals}-{match.away_goals}")

        if match.home_goals == match.away_goals:
            print(f"Match {match.id} is a draw. Checking phase for penalties...")
            if current_euro_season.current_phase == 'knockout':
                print(f"Knockout phase detected. Processing penalties for match {match.id}.")
                process_penalties(match)
        else:
            print(f"Match {match.id} has a winner. Finalizing...")
            finalize_match(match)
            print(f"Match {match.id} finalized. Updating season statistics...")
            update_season_statistics_for_match(match)

    if current_euro_season.current_phase == 'group':
        print("Group phase detected. Checking if group stage matches are finished...")
        if not are_group_stage_matches_finished(current_euro_season):
            print("Group stage matches are not finished. Updating standings...")
            update_euro_cup_standings(match_date.date)
        else:
            print("Group stage matches are finished. Advancing teams from groups...")
            advance_teams_from_groups(current_euro_season)
            current_euro_season.current_phase = 'knockout'
            current_euro_season.save()
            print("Phase changed to knockout. Generating knockout matches...")

            free_date = MatchSchedule.objects.filter(
                season=current_euro_season.season,
                event_type='euro',
                is_euro_cup_day_assigned=False,
                is_played=False
            ).order_by('date').first()

            if not free_date:
                print(f"No available date for EuropeanCupSeason {current_euro_season}.")
                return

            print(f"Generating knockout matches on date {free_date.date}.")
            generate_euro_cup_knockout(current_euro_season, free_date.date)
            free_date.is_euro_cup_day_assigned = True
            free_date.save()

    elif current_euro_season.current_phase == 'knockout':
        print("Knockout phase detected. Checking current knockout stage...")
        current_stage_order = get_current_knockout_stage_order(current_euro_season)
        print(f"Current stage order: {current_stage_order}")

        if not are_knockout_matches_finished(current_euro_season, current_stage_order):
            print(f"Knockout matches for stage {current_stage_order} are still ongoing.")
            return

        else:
            print(f"Knockout matches for stage {current_stage_order} are completed. Proceeding to next stage...")
            free_date = MatchSchedule.objects.filter(
                season=current_euro_season.season,
                event_type='euro',
                is_euro_cup_day_assigned=False,
                is_played=False
            ).order_by('date').first()

            if not free_date:
                print(f"No available date for next knockout stage in {current_euro_season}.")
                return

            print(f"Generating next knockout stage matches on date {free_date.date}.")
            generate_euro_cup_knockout(current_euro_season, free_date.date)
            free_date.is_euro_cup_day_assigned = True
            free_date.save()

def process_match(match):
    print(f"Starting to process match ID: {match.id}")
    with transaction.atomic():
        try:
            print("Ensuring team tactics...")
            ensure_team_tactics(match)

            print("Generating player match stats...")
            generate_players_match_stats(match)

            total_minutes = 90
            current_minute = match.current_minute

            while current_minute < total_minutes:
                print(f"Updating match minute: {current_minute}")
                current_minute = update_match_minute(match)

                print("Determining team with initiative...")
                team_with_initiative = get_match_team_initiative(match)

                print("Choosing random player for event...")
                random_player = choose_event_random_player(team_with_initiative)

                print("Getting random match event...")
                event = get_random_match_event()
                print(f'Event: {event}')

                success = calculate_event_success_rate(event, random_player)
                print(f'Success: {success}')

                print("Fetching EventResult...")
                event_result = get_event_result(event, success)

                if event_result.event_result in ["YellowCard", "RedCard"]:
                    print(f"Handling card event: {event_result.event_result}")
                    handle_card_event(event_result, random_player, match, team_with_initiative)
                else:
                    print("Updating player stats...")
                    update_player_stats_from_template(match, event_result, random_player)

                    print("Fetching EventTemplate...")
                    template = get_event_template(event_result)

                    if not template:
                        print("No Template found. Skipping template-related processing.")
                        continue

                    print("Formatting event template...")
                    formatted_template = fill_template_with_player(template, random_player)

                    print("Logging match event...")
                    log_match_event(match, current_minute, template, formatted_template, random_player)

                    print("Updating match score...")
                    update_match_score(event_result, match, team_with_initiative)

                    print("Checking initiative...")
                    check_initiative(template, match)

                print(f"Saving match state at minute: {current_minute}")
                match.current_minute = current_minute
                match.save()

        except Exception as e:
            print(f"Error processing match ID {match.id}: {e}")
            raise


def process_penalties(match):
    print("Initializing penalty shootout...")
    # Initialize the penalty shootout
    match_penalties = generate_match_penalties(match)

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
    team_with_initiative = match_penalties.current_initiative

    while not match_penalties.is_completed:
        print(f"Team with initiative: {team_with_initiative.name}")
        current_team = team_with_initiative
        current_data = team_data[current_team]

        print(f"Checking rotation violations for team {current_team.name}...")
        # Check for player rotation violations and reset order if all players have taken penalties
        if check_rotation_violations(current_team, current_data["taken_penalty_players"]):
            print(f"Starting a new round for team {current_team.name}")
            current_data["execution_order"] = get_starting_lineup(current_team)
            current_data["taken_penalty_players"] = []

        print(f"Getting next player for team {current_team.name}...")
        # Get the next player to take a penalty
        penalty_taker_id = current_data["execution_order"].pop(0)
        penalty_taker = get_penalty_taker(current_team, current_data["taken_penalty_players"])

        print(f"Player {penalty_taker.name} from team {current_team.name} is taking the penalty.")

        print("Generating penalty match event...")
        event = get_penalty_match_event()

        print("Calculating success rate...")
        success = calculate_event_success_rate(event, penalty_taker)

        print("Determining event result...")
        event_result = get_event_result(event, success)

        print("Is it Goal...?")
        is_goal = calculate_penalty_success(success, event_result.event_threshold)

        print("Generating event template...")
        template = get_event_template(event_result)
        formatted_template = fill_template_with_player(template, penalty_taker)

        # Log penalty result
        print(f"Penalty Result: {formatted_template}")
        log_penalty_event(match, formatted_template, penalty_taker, success)

        print("Updating penalty shootout score...")
        update_penalty_score(match_penalties, success, current_team)

        print("Saving penalty attempt...")
        # Save the penalty attempt
        attempt_order = len(match_penalties.attempts.all()) + 1
        PenaltyAttempt.objects.create(
            match_penalty=match_penalties,
            player=penalty_taker,
            is_goal=is_goal,
            attempt_order=attempt_order,
            team=current_team
        )

        print(f"Tracking player {penalty_taker.name} who took the penalty...")
        # Track the player who took the penalty
        current_data["taken_penalty_players"].append(penalty_taker.id)

        print("Checking if penalty shootout is complete...")
        # Check if the penalty shootout is complete
        if check_penalties_completion(match_penalties):
            print("Penalty shootout completed!")
            break

        print("Updating initiative to switch teams...")
        update_penalty_initiative(match_penalties)
        team_with_initiative = match_penalties.current_initiative
        print(f"Next team to take a penalty: {team_with_initiative.name}")
