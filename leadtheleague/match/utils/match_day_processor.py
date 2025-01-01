from datetime import date
from django.db import transaction
from game.models import MatchSchedule
from match.models import Match
from match.utils.generate_match_stats_utils import generate_players_match_stats
from match.utils.match_helpers import update_match_minute, get_match_team_initiative, choose_event_random_player, \
    get_match_event_attributes_weight, get_event_success_rate, get_match_event_template, get_event_players, \
    get_random_match_event, fill_template_with_players, update_player_stats_from_template, log_match_event, \
    finalize_match, check_initiative, update_match_score
from players.utils.get_player_stats_utils import get_player_attributes
from players.utils.update_player_stats_utils import update_season_stats_from_match
from teams.utils.lineup_utils import ensure_team_tactics

def match_day_processor():
    today = date.today()
    schedule = MatchSchedule.objects.filter(date=today).first()

    if not schedule:
        print(f"No schedule found for today ({today}).")
        return

    print(f"Processing match day for {today}: {schedule.event_type}")

    with transaction.atomic():
        try:
            if schedule.event_type == 'league':
                process_league_day(schedule)
            elif schedule.event_type == 'cup':
                process_cup_day(schedule)
            elif schedule.event_type == 'euro':
                process_euro_day(schedule)
            else:
                print(f"Unknown event type: {schedule.event_type}")
                return

            schedule.is_played = True
            schedule.save()

        except Exception as e:
            print(f"Error processing match day: {e}")
            return

    print(f"Match day processing completed for {today}.")


def process_league_day(schedule):
    print("Processing league matches...")
    matches = Match.objects.filter(
        season=schedule.season,
        league_season__isnull=False,
        match_date=schedule.date,
        is_played=False
    )

    for match in matches:
        process_match(match)

    # Update standings here if needed


def process_cup_day(schedule):
    print("Processing cup matches...")
    matches = Match.objects.filter(
        season=schedule.season,
        season_cup__isnull=False,
        match_date=schedule.date,
        is_played=False
    )

    for match in matches:
        process_match(match)

    # Handle next round draw or finalize cup if needed


def process_euro_day(schedule):
    print("Processing European cup matches...")
    matches = Match.objects.filter(
        season=schedule.season,
        european_cup_season__isnull=False,
        match_date=schedule.date,
        is_played=False
    )

    for match in matches:
        process_match(match)

    # Update standings or handle knockout stages


def process_match(match):
    with transaction.atomic():
        try:
            ensure_team_tactics(match)
            generate_players_match_stats(match)

            total_minutes = 90
            current_minute = match.current_minute

            while current_minute < total_minutes:
                current_minute = update_match_minute(match, current_minute)
                team_with_initiative = get_match_team_initiative(match)
                random_player = choose_event_random_player(team_with_initiative)

                player_attributes = get_player_attributes(random_player)
                event = get_random_match_event()
                attributes_and_weights = get_match_event_attributes_weight(event, player_attributes)
                success = get_event_success_rate(event, attributes_and_weights)
                template = get_match_event_template(event.id, success)

                event_players = get_event_players(template, random_player, team_with_initiative)
                formatted_template = fill_template_with_players(template, event_players)

                update_player_stats_from_template(match, template, event_players)
                log_match_event(match, current_minute, template, formatted_template, event_players)
                update_match_score(template, match, team_with_initiative)
                check_initiative(template, match)

                match.current_minute = current_minute
                match.save()

            finalize_match(match)
            update_season_stats_from_match(match)

        except Exception as e:
            print(f"Error processing match {match.id}: {e}")
            raise
