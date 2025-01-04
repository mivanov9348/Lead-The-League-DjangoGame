from cups.models import SeasonCup
from cups.utils.generate_cup_fixtures import generate_next_round_fixtures
from cups.utils.update_cup_season import populate_progressing_team
from europeancups.utils.euro_cup_season_utils import get_current_european_cup_season, get_current_knockout_stage_order, \
    are_knockout_matches_finished
from europeancups.utils.group_stage_utils import update_euro_cup_standings, are_group_stage_matches_finished, \
    advance_teams_from_groups
from europeancups.utils.knockout_utils import generate_euro_cup_knockout
from fixtures.utils import transfer_match_to_fixture
from game.models import MatchSchedule
from leagues.utils import update_standings_from_fixtures
from match.models import Match, PenaltyAttempt
from match.utils.generate_match_stats_utils import generate_players_match_stats, generate_match_penalties
from match.utils.match_helpers import update_match_minute, get_match_team_initiative, choose_event_random_player, \
    get_match_event_attributes_weight, get_event_success_rate, get_random_match_event, log_match_event, finalize_match, \
    check_initiative, \
    update_match_score, handle_card_event, update_player_stats_from_template, fill_template_with_player, \
    get_event_result, get_event_template
from match.utils.match_penalties_helpers import get_penalty_taker, update_penalty_score, check_penalties_completion, \
    update_penalty_initiative, log_penalty_event, check_rotation_violations
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

    fixtures = []
    for match in matches:
        process_match(match)
        update_season_statistics_for_match(match)
        finalize_match(match)

    if fixtures:
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
            finalize_match(match)
            update_season_statistics_for_match(match)

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
    print("Processing European cup matches...")
    current_euro_season = get_current_european_cup_season()
    matches = Match.objects.filter(
        season=match_date.season,
        european_cup_season__isnull=False,
        match_date=match_date.date,
        is_played=False
    )

    for match in matches:
        process_match(match)
        if match.home_goals == match.away_goals:
            if current_euro_season.current_phase == 'knockout':
                process_penalties(match)
        else:
            finalize_match(match)
            update_season_statistics_for_match(match)

    if current_euro_season.current_phase == 'group':
        if not are_group_stage_matches_finished(current_euro_season):
            update_euro_cup_standings(match_date)
        else:
            advance_teams_from_groups(current_euro_season)
            current_euro_season.current_phase = 'knockout'
            current_euro_season.save()

            free_date = MatchSchedule.objects.filter(
                season=current_euro_season.season,
                event_type='euro',
                is_euro_cup_day_assigned=False,
                is_played=False
            ).order_by('date').first()

            if not free_date:
                print(f"No available date for EuropeanCupSeason {current_euro_season}.")
                return

            generate_euro_cup_knockout(current_euro_season, free_date.date)

            free_date.is_euro_cup_day_assigned = True
            free_date.save()

    elif current_euro_season.current_phase == 'knockout':
        current_stage_order = get_current_knockout_stage_order(current_euro_season)
        if not are_knockout_matches_finished(current_euro_season, current_stage_order):
            print(f"Knockout matches for stage {current_stage_order} are still ongoing.")
            return

        else:
            free_date = MatchSchedule.objects.filter(
                season=current_euro_season.season,
                event_type='euro',
                is_euro_cup_day_assigned=False,
                is_played=False
            ).order_by('date').first()

            if not free_date:
                print(f"No available date for next knockout stage in {current_euro_season}.")
                return

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

                print(f"Getting attributes for player ID: {random_player.id}")
                player_attributes = get_player_attributes(random_player)

                print("Getting random match event...")
                event = get_random_match_event()
                print(f'Event: {event}')

                print(f"Calculating success rate for event: {event.type}")
                attributes_and_weights = get_match_event_attributes_weight(event, player_attributes)
                success = get_event_success_rate(event, attributes_and_weights)
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
    # Initialize the penalty shootout
    match_penalties = generate_match_penalties(match)

    home_taken_penalty_players = []
    away_taken_penalty_players = []

    home_execution_order = []
    away_execution_order = []

    # Determine which team starts the penalty shootout
    team_with_initiative = match.home_team

    while not match_penalties.is_completed:
        current_team = team_with_initiative

        # Track players who have taken penalties for the current team
        taken_penalty_players = (
            home_taken_penalty_players if current_team == match.home_team else away_taken_penalty_players
        )

        # Maintain execution order for the current team
        execution_order = (
            home_execution_order if current_team == match.home_team else away_execution_order
        )

        # Check for player rotation violations and reset order if all players have taken penalties
        if check_rotation_violations(current_team, taken_penalty_players):
            print(f"Starting a new round for team {current_team.name}")
            execution_order.clear()
            execution_order.extend([player.id for player in current_team.player_set.all()])

        # Get the next player to take a penalty
        penalty_taker_id = execution_order.pop(0)
        penalty_taker = get_penalty_taker(current_team, taken_penalty_players)

        # Retrieve the player's attributes and calculate success probabilities
        player_attributes = get_player_attributes(penalty_taker)
        event = get_random_match_event(event_type='Penalty')
        attributes_and_weights = get_match_event_attributes_weight(event, player_attributes)
        success = get_event_success_rate(event, attributes_and_weights)

        event_result = get_event_result(event, success)
        template = get_event_template(event_result)

        formatted_template = fill_template_with_player(template, penalty_taker)
        log_penalty_event(match, formatted_template, penalty_taker, success)

        # Update the penalty shootout score
        update_penalty_score(match_penalties, success, current_team)

        # Save the penalty attempt
        attempt_order = len(match_penalties.attempts.all()) + 1
        PenaltyAttempt.objects.create(
            match_penalty=match_penalties,
            player=penalty_taker,
            is_goal=success,
            attempt_order=attempt_order,
            team=current_team
        )

        # Track the player who took the penalty
        taken_penalty_players.append(penalty_taker.id)

        # Check if the penalty shootout is complete
        if check_penalties_completion(match_penalties):
            print("Penalty shootout completed!")
            break

        # Update the initiative to switch teams
        update_penalty_initiative(match_penalties)
        team_with_initiative = match_penalties.current_initiative
