import datetime
from django.db import transaction, IntegrityError

from cups.utils.generate_cup_fixtures import process_all_season_cups, populate_season_cups_with_teams
from cups.utils.update_cup_season import generate_cups_season
from europeancups.utils.euro_cup_season_utils import generate_european_cups_season, europe_promotion
from europeancups.utils.group_stage_utils import create_groups_for_season, generate_group_fixtures
from fixtures.utils import  generate_all_league_fixtures
from game.models import Season
from game.utils.get_season_stats_utils import check_are_all_competition_completed
from leagues.utils import generate_leagues_season, populate_teams_for_season
from match.utils.generate_match_stats_utils import generate_league_matches, generate_cup_matches, \
    generate_euro_cup_matches
from messaging.utils.category_messages_utils import create_message_for_new_season
from messaging.utils.placeholders_utils import get_new_season_placeholders
from players.utils.generate_player_utils import generate_youth_players, process_retirement_players, \
    generate_all_players_season_stats, generate_players_for_all_teams
from players.utils.get_player_stats_utils import ensure_all_teams_has_minimum_players
from players.utils.update_player_stats_utils import promoting_youth_players
from staff.utils.agent_utils import generate_agents
from staff.utils.coach_utils import new_seasons_coaches
from teams.utils.generate_team_utils import set_team_logos

def create_game_season(year, season_number, start_date, match_time, is_active):
    start_datetime = datetime.datetime.combine(start_date, match_time)

    if Season.objects.filter(year=year, season_number=season_number).exists():
        return None, "Season already exists!"

    try:
        with transaction.atomic():
            if is_active:
                Season.objects.filter(is_active=True).update(is_active=False)

            new_season = Season.objects.create(
                year=year,
                season_number=season_number,
                start_date=start_datetime,
                match_time=match_time,
                is_active=is_active
            )

            generate_leagues_season(new_season)
            generate_cups_season(new_season)
            generate_european_cups_season(new_season)
            placeholders = get_new_season_placeholders(new_season)

            create_message_for_new_season(
                category='new season',
                placeholders=placeholders,
                is_global=True
            )

        return new_season, "Season created successfully!"
    except IntegrityError as e:
        return None, f"Error creating season: {str(e)}"

def finalize_season(season):
    if not check_are_all_competition_completed(season):
        return False

    season.is_ended = True
    season.is_active = False
    season.end_date = datetime.date.today()
    season.save()
    return True

def prepare_first_season(season):
    try:
        with transaction.atomic():
            # PopulateWithTeams
            populate_teams_for_season(season)
            print(f'Teams are added successfully')
            # Add Logo To Teams
            set_team_logos()
            print(f'Logos Add Successfully')
            # Populate Season Cups With Teams
            populate_season_cups_with_teams(season)
            # populate euro cup with teams
            europe_promotion(season)
            print(f'European teams found!')
            # league season fixtures
            generate_all_league_fixtures(season)
            print(f'League Fixtures Successfully Created!')
            # cup season fixtures
            process_all_season_cups(season)
            print(f'Cup Fixtures Successfully Created!')
            # eurocup season fixtures
            create_groups_for_season(season)
            print(f'European Cup Group Successfully Created!')
            generate_group_fixtures(season)
            print(f'European Cup Group Fixtures Successfully Created!')
            # Players in all teams:
            generate_players_for_all_teams()
            print(f'Players are added to Teams')
            # Generate Player Season Stats:
            generate_all_players_season_stats()
            print(f'Players Season Stats Updated!')
            # New Youth Intake
            generate_youth_players(season)
            print(f'New youth players generated!')
            # coaches
            new_seasons_coaches()
            print('Coaches for new season added successfully!')
            # agents
            generate_agents()
            print(f'Agents added successfully!')
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def prepare_new_season(new_season):
    try:
        with transaction.atomic():
            # eurocup participants
            europe_promotion(new_season)
            print(f'European teams found!')
            # retired players
            process_retirement_players()
            print(f'Players over 35 years successfully retired!')
            # league season fixtures
            generate_all_league_fixtures(new_season)
            print(f'League Fixtures Successfully Created!')
            # cup season fixtures
            process_all_season_cups(new_season)
            print(f'Cup Fixtures Successfully Created!')
            # eurocup season fixtures
            create_groups_for_season(new_season)
            print(f'European Cup Group Successfully Created!')
            generate_group_fixtures(new_season)
            print(f'European Cup Group Fixtures Successfully Created!')
            # LeagueMatches
            generate_league_matches(new_season)
            print(f'Generate League Matches')
            # CupMatches
            generate_cup_matches(new_season)
            print(f'Generate Cup Matches')
            # EuroCupMatches
            generate_euro_cup_matches(new_season)
            print(f'Generate Euro Cup Matches')
            # promote youth players
            promoting_youth_players()
            print(f'Youth Players over 18 are now mens!')
            # ensure all teams has enough players
            ensure_all_teams_has_minimum_players()
            print(f'All Teams are ready with players!')
            # New Youth Intake
            generate_youth_players(new_season)
            print(f'New youth players generated!')
            # playerseasonstats
            generate_all_players_season_stats()
            print(f'Players Season Stats Updated!')
            # coaches
            new_seasons_coaches()
            print('Coaches for new season added successfully!')
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
