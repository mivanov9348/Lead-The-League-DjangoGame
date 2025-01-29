import datetime
import random
from datetime import time

from django.core.management.base import BaseCommand
import logging
import random

from django.db.models import Q
from numpy.ma.extras import average

from core.models import FirstName
from core.utils.names_utils import get_random_first_name
from cups.models import SeasonCup
from europeancups.models import EuropeanCup, EuropeanCupSeason
from europeancups.utils.euro_cup_season_utils import finalize_euro_cup
from game.models import MatchSchedule
from game.utils.get_season_stats_utils import get_current_season
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
from staff.models import FootballAgent
from staff.utils.agent_utils import scouting_new_talents, generate_agents, attach_image_to_all_agents
from teams.models import Team
from teams.utils.lineup_utils import ensure_team_tactics
from teams.utils.team_analytics_utils import process_league_season_data, get_league_season_statistics, plot_team_points, \
    plot_goals_scored, plot_points_vs_goal_difference
from teams.utils.team_finance_utils import get_teams_by_balance, team_income, team_match_profit


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")

        # # match = Match.objects.filter(id = 151542).first()
        #
        # matches = Match.objects.filter(match_date = '2025-04-21')
        #
        # for match in matches:
        #     ensure_team_tactics(match)

        # match_days = MatchSchedule.objects.filter(event_type='euro', is_played=False).order_by('date')
        # try:
        #     for match_day in match_days:
        #         match_day_processor(match_day.date)
        #
        # except:
        #     print('Error when processing')

        # match_days = MatchSchedule.objects.filter(event_type='cup', is_played=False).order_by('date')
        #
        # try:
        #     for match_day in match_days:
        #         match_day_processor(match_day.date)
        #
        # except:
        #     print('Error when processing')

        # match_days = MatchSchedule.objects.filter(event_type='league', is_played=False).order_by('date')
        # try:
        #     dayslimit = 4
        #     for i, match_day in enumerate(match_days):
        #         if i >= dayslimit:
        #             print(f"Reached maximum iterations: {dayslimit}")
        #             print(datetime.datetime.now())
        #             break
        #
        #         print(f"Processing match day {i + 1}/{dayslimit}: {match_day.date}")
        #         match_day_processor(match_day.date)
        #
        # except:
        #     print('Error when processing')

        season = get_current_season()
        match_days = MatchSchedule.objects.filter(season=season, is_played=False).exclude(
            event_type='transfer').order_by('date')
        try:
            dayslimit = 2
            for i, match_day in enumerate(match_days):
                if i >= dayslimit:
                    print(f"Reached maximum iterations: {dayslimit}")
                    print(datetime.datetime.now())
                    break

                print(f"Processing match day {i + 1}/{dayslimit}: {match_day.date}")
                match_day_processor(match_day.date)

        except:
            print('Error when processing')

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
        # set_manual_day_today('2025-05-01')
        # finalize_euro_cup(current_euro_season, match)
