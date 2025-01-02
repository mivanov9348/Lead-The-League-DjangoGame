from datetime import date
from django.db import transaction

from cups.models import SeasonCup
from cups.utils.generate_cup_fixtures import generate_next_round_fixtures
from cups.utils.update_cup_season import populate_progressing_team
from europeancups.utils.euro_cup_season_utils import get_current_european_cup_season, get_current_knockout_stage_order, \
    are_knockout_matches_finished
from europeancups.utils.group_stage_utils import update_euro_cup_standings, are_group_stage_matches_finished, \
    advance_teams_from_groups
from europeancups.utils.knockout_utils import generate_euro_cup_knockout
from game.models import MatchSchedule
from leagues.utils import update_standings_from_fixtures
from match.models import Match
from match.utils.generate_match_stats_utils import generate_players_match_stats
from match.utils.match_helpers import update_match_minute, get_match_team_initiative, choose_event_random_player, \
    get_match_event_attributes_weight, get_event_success_rate, get_match_event_template, get_event_players, \
    get_random_match_event, fill_template_with_players, update_player_stats_from_template, log_match_event, \
    finalize_match, check_initiative, update_match_score
from players.utils.get_player_stats_utils import get_player_attributes
from players.utils.player_analytics_utils import update_season_analytics
from players.utils.update_player_stats_utils import update_season_stats_from_match
from teams.utils.lineup_utils import ensure_team_tactics


def match_day_processor():
    today = date.today()
    match_date = MatchSchedule.objects.filter(date=today).first()

    if not match_date:
        print(f"No schedule found for today ({today}).")
        return

    print(f"Processing match day for {today}: {match_date.event_type}")

    with transaction.atomic():
        try:
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
        process_match(match)  # Обработваме мача
        if match.fixture:
            fixtures.append(match.fixture)

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

    next_available_date = MatchSchedule.objects.filter(
        season=match_date.season,
        event_type='cup',
        is_cup_day_assigned=False,
        date__gt=match_date.date  # Уверяваме се, че е бъдеща дата
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

    # Handle group stage
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

    # Handle knockout stage
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

            if match.home_goals == match.away_goals:
                penalties()
            else:
                finalize_match(match)
                update_season_stats_from_match(match)

        except Exception as e:
            print(f"Error processing match {match.id}: {e}")
            raise

def penalties():
    pass