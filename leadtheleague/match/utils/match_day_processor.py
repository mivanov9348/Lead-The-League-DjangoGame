from cups.models import SeasonCup
from cups.utils.generate_cup_fixtures import generate_next_round_fixtures
from cups.utils.update_cup_season import populate_progressing_team
from europeancups.utils.euro_cup_season_utils import get_current_european_cup_season, get_current_knockout_stage_order
from europeancups.utils.group_stage_utils import update_euro_cup_standings, advance_teams_from_groups, \
    update_group_stage_status_if_finished, are_group_stage_matches_finished
from europeancups.utils.knockout_utils import generate_euro_cup_knockout, finish_current_knockout_stage
from fixtures.utils import transfer_match_to_fixture, get_fixtures_by_date
from game.models import MatchSchedule, GameState
from leagues.utils import update_standings_from_fixtures
from match.models import Match, PenaltyAttempt
from match.utils.generate_match_stats_utils import generate_players_match_stats, generate_match_penalties
from match.utils.get_match_stats import calculate_match_attendance
from match.utils.lineup_utils import get_starting_lineup
from match.utils.match_events_utils import create_kickoff_match_event, create_match_end_match_event, \
    create_penalty_start_match_event, get_random_match_event, calculate_event_success_rate, get_event_result, \
    get_event_template, log_match_event
from match.utils.match_helpers import log_match_participate, finalize_match, update_match_minute, \
    get_match_team_initiative, choose_event_random_player, update_player_stats_from_template, handle_card_event, \
    fill_template_with_player, check_initiative, update_match_score
from match.utils.match_penalties_helpers import get_penalty_taker, update_penalty_score, check_penalties_completion, log_penalty_event, check_rotation_violations, get_penalty_match_event, \
    calculate_penalty_success, check_sudden_death_completion
from messaging.utils.notifications_utils import create_match_notifications
from players.utils.player_analytics_utils import update_season_analytics
from players.utils.update_player_stats_utils import update_season_statistics_for_match, update_match_player_ratings
from teams.utils.lineup_utils import ensure_team_tactics
from django.db import transaction
from teams.utils.team_analytics_utils import bulk_update_team_statistics


def match_day_processor(date=None):
    today = date if date else date.today()
    match_date = MatchSchedule.objects.filter(date=today).first()

    if not match_date:
        print(f"No schedule found for today ({today}).")
        return

    if match_date.is_played:
        print(f"Match day for {today} has already been processed.")
        return

    print(f"Processing match day for {today}: {match_date.event_type}")

    try:
        game_state, created = GameState.objects.get_or_create(id=1)
        game_state.is_playing_matches = True
        game_state.save()
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
        game_state.is_playing_matches = False
        game_state.save()
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
        update_match_player_ratings(match)
        log_match_participate(match)
        finalize_match(match)
        bulk_update_team_statistics(matches, match_date)

    fixtures = get_fixtures_by_date(match_date.date)
    update_standings_from_fixtures(fixtures)

def process_cup_day(match_date):
    print("Processing cup matches...")

    try:
        matches = Match.objects.filter(
            season=match_date.season,
            season_cup__isnull=False,
            match_date=match_date.date,
            is_played=False
        )
        if not matches.exists():
            print(f"No matches to process for date: {match_date.date}")
            return
    except Exception as e:
        print(f"Error fetching matches for cup day on {match_date.date}: {e}")
        return

    for match in matches:
        try:
            print(f"Processing match: {match.id}")
            process_match(match)
            print(f"Match {match.id} processed successfully.")
        except Exception as e:
            print(f"Error processing match {match.id}: {e}")
            continue

        try:
            create_match_end_match_event(match)
            print(f"Match end event created for match {match.id}.")
        except Exception as e:
            print(f"Error creating match end event for match {match.id}: {e}")

        try:
            if match.home_goals == match.away_goals:
                print(f"Match {match.id} ended in a draw. Initiating penalties.")
                create_penalty_start_match_event(match)
                process_penalties(match)
                print(f"Penalties processed for match {match.id}.")
            else:
                print(f"Updating statistics for match {match.id}.")
                update_season_statistics_for_match(match)
                update_match_player_ratings(match)
                print(f"Statistics updated for match {match.id}.")
        except Exception as e:
            print(f"Error updating or processing penalties for match {match.id}: {e}")

        try:
            finalize_match(match)
            print(f"Match {match.id} finalized successfully.")
        except Exception as e:
            print(f"Error finalizing match {match.id}: {e}")

        try:
            log_match_participate(match)
            print(f"Match participation logged for match {match.id}.")
        except Exception as e:
            print(f"Error logging match participation for match {match.id}: {e}")

    bulk_update_team_statistics(matches, match_date)
    try:
        print("Team statistics updated successfully.")
    except Exception as e:
        print(f"Error updating team statistics: {e}")

    try:
        next_available_date = MatchSchedule.objects.filter(
            season=match_date.season,
            event_type='cup',
            is_cup_day_assigned=False,
            date__gt=match_date.date
        ).order_by('date').first()
    except Exception as e:
        print(f"Error fetching the next available cup day: {e}")
        return

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
            print(f"{season_cup.cup.name} fixtures generated successfully.")
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

        if match.home_goals == match.away_goals and current_euro_season.current_phase == 'knockout':
            print(f"Match {match.id} is a draw in the knockout phase. Processing penalties...")
            process_penalties(match)
        else:
            print(f"Match {match.id} finalized. Updating season statistics...")
            update_season_statistics_for_match(match)
            print(f'update match ratings')
            update_match_player_ratings(match)

        print(f'match attendance')
        calculate_match_attendance(match)
        print(f'log_match_participate')
        log_match_participate(match)
        print(f'finalize_matc')
        finalize_match(match)
        bulk_update_team_statistics(matches, match_date)

    if current_euro_season.current_phase == 'group':
        print("Group phase detected. Checking if group stage matches are finished...")
        if not are_group_stage_matches_finished(current_euro_season):
            print("Group stage matches are not finished. Updating standings...")
            update_euro_cup_standings(match_date.date)

            if update_group_stage_status_if_finished(current_euro_season):
                print("Group stage matches are now finished. Advancing teams from groups...")
                advance_teams_from_groups(current_euro_season)

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
        else:
            print("Group stage matches are finished. Advancing teams from groups...")
            advance_teams_from_groups(current_euro_season)

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
        print(f'Current stage: {current_stage_order}')
        finish_current_knockout_stage(current_stage_order)
        print(f"Knockout matches for stage {current_stage_order} are completed. Proceeding to next stage...")

        free_date = MatchSchedule.objects.filter(
            season=current_euro_season.season,
            event_type='euro',
            is_euro_cup_day_assigned=False,
            is_played=False
        ).order_by('date').first()
        print(f'Free date: {free_date}')

        if not free_date:
            print(f"No available date for next knockout stage in {current_euro_season}.")
            return

        # 4. Generate next knockout
        print(f"Generating next knockout stage matches on date {free_date.date}.")
        generate_euro_cup_knockout(current_euro_season, free_date.date)

        print(f'Finished generating Euro Cup knockout matches.')
        free_date.is_euro_cup_day_assigned = True
        free_date.save()

        print("Updated free_date to is_euro_cup_day_assigned = True.")


def process_match(match):
    print(f"Starting to process match ID: {match.id}")
    with transaction.atomic():
        try:
            print("Ensuring team tactics...")
            ensure_team_tactics(match)

            print("Generating player match stats...")
            generate_players_match_stats(match)

            print('Create Kickoff Message!')
            create_kickoff_match_event(match)

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
                    update_match_score(event_result, match, team_with_initiative, random_player)

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
