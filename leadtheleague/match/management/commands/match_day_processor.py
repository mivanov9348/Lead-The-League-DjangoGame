import datetime
import random
from datetime import time
import logging
import random

from django.core.management import BaseCommand
from django.db.models import Q
from numpy.ma.extras import average
from core.models import FirstName
from core.utils.names_utils import get_random_first_name
from cups.models import SeasonCup
from europeancups.models import EuropeanCup, EuropeanCupSeason
from europeancups.utils.euro_cup_season_utils import finalize_euro_cup
from game.models import MatchSchedule
from game.utils.get_season_stats_utils import get_current_season
from game.utils.schedule_utils import advance_day
from game.utils.season_functionalities_utils import set_manual_day_today
from leagues.models import LeagueSeason, League
from leagues.utils import auto_set_league_champions
from match.models import Match
from match.utils.match.attendance import calculate_match_attendance, calculate_match_income
from match.utils.match.events import calculate_event_success_rate, get_random_match_event, get_event_result
from match.utils.match.processing import match_day_processor, process_match
from match.utils.match.stats import generate_players_match_stats
from messaging.utils.category_messages_utils import create_league_champion_message, create_cup_champion_message, \
    create_european_cup_champion_message
from players.models import Player
from players.utils.generate_player_utils import generate_random_player
from players.utils.get_player_stats_utils import ensure_all_teams_has_minimum_players
from staff.models import FootballAgent, Coach
from staff.utils.agent_utils import scouting_new_talents, generate_agents, attach_image_to_all_agents
from teams.ai.hire_coach_and_train_ai import ai_manage_coaches_and_training, ai_train_players, ai_assign_coach
from teams.ai.release_player_ai import ai_decide_release_players
from teams.ai.search_player_ai import search_player_decision_making
from teams.models import Team
from teams.state import TeamState
from teams.utils.lineup_utils import ensure_team_tactics
from teams.utils.team_analytics_utils import process_league_season_data, get_league_season_statistics, plot_team_points, \
    plot_goals_scored, plot_points_vs_goal_difference
from teams.utils.team_finance_utils import get_teams_by_balance, team_income, team_match_profit


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")

        try:
            overall_start_time = datetime.datetime.now()
            print(f"Overall process started at: {overall_start_time}")

            days_step = 1

            season = get_current_season()

            for _ in range(days_step):
                advance_day()

                season.refresh_from_db()
                current_date = season.current_date
                print(f"Processing matches for date: {current_date}")

                match_days = MatchSchedule.objects.filter(season=season, date=current_date, is_played=False).exclude(
                    event_type='transfer'
                )

                if not match_days.exists():
                    print(f"No matches found for {current_date}, skipping.")
                    continue

                for match_day in match_days:
                    start_time = datetime.datetime.now()
                    print(f"Processing match: {match_day} at {start_time}")

                    match_day_processor(match_day.date)

                    end_time = datetime.datetime.now()
                    duration = end_time - start_time
                    print(f"Finished processing match: {match_day} at {end_time}, Duration: {duration}")

                if current_date >= season.end_date:
                    print("Season has ended. Stopping process.")
                    break

            overall_end_time = datetime.datetime.now()
            overall_duration = overall_end_time - overall_start_time
            print(f"Overall process finished at: {overall_end_time}, Total duration: {overall_duration}")

        except Exception as e:
            print(f'Error when processing: {e}')

        # first_name = get_random_first_name('Eastern Europe','Bulgaria')
        # print(first_name)
        # generate_random_player()
        # team = Team.objects.filter(id=12533).first()
        # team_income(team, 2000000, "Test")

        # matches = Match.objects.filter(match_date='2025-03-11')
        # for match in matches:
        #     team_match_profit(match.home_team, match, 2000000, 'test')

        # current_season = get_current_season()
        # df = process_league_season_data(current_season)
        #
        # if df is not None:
        #     # Визуализираме точките
        #     plot_team_points(df)
        #
        #     # Визуализираме отбелязаните голове
        #     plot_goals_scored(df)
        #
        #     # Визуализираме точките спрямо разлика в головете
        #     plot_points_vs_goal_difference(df)

        # match = Match.objects.filter(id = 170168).first()
        # process_match(match)

        # success_rates = []
        # for i in range(0, 50):
        #     print('----------------------------')
        #     event = get_random_match_event()
        #     print(f'Event: {event}')
        #     players = Player.objects.all()
        #     player = random.choice(players)
        #     print(f'Player: {player.first_name} {player.last_name} - {player.position.name}')
        #     success = calculate_event_success_rate(event, player)
        #     print(f'Success: {success}')
        #     success_rates.append(success)
        #     event_result = get_event_result(event, success)
        #     print(f'event result: {event_result.event_result}')
        #
        # print(f'average for 50: {average(success_rates)}')
        # generate_agents(1)
        # attach_image_to_all_agents()
        # agents = FootballAgent.objects.all()
        # for agent in agents:
        #     agents_sell = get_agent_sold_players(agent)
        #     sum_get = get_agent_total_transfer_income(agent)
        #     print(f'Agent: {agent.first_name} {agent.last_name} - agent sell: {agents_sell['count']}, Sum: {sum_get}')
        # set_manual_day_today('2025-01-30')
        # finalize_euro_cup(current_euro_season, match)

        # season = get_current_season()
        # TeamState.process_all_teams(season)