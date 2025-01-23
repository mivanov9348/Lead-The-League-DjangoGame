import random

from django.core.management.base import BaseCommand

from core.models import FirstName
from core.utils.names_utils import get_random_first_name
from game.models import MatchSchedule
from game.utils.season_functionalities_utils import set_manual_day_today
from leagues.utils import auto_set_league_champions
from match.models import Match
from match.utils.match.attendance import calculate_match_attendance, calculate_match_income
from match.utils.match.processing import match_day_processor
from match.utils.match.stats import generate_players_match_stats
from players.utils.generate_player_utils import generate_random_player
from players.utils.get_player_stats_utils import ensure_all_teams_has_minimum_players
from staff.utils.agent_utils import scouting_new_talents, generate_agents
from teams.models import Team
from teams.utils.lineup_utils import ensure_team_tactics
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

        match_days = MatchSchedule.objects.filter(event_type='league', is_played=False).order_by('date')
        try:
            dayslimit = 5
            for i, match_day in enumerate(match_days):
                if i >= dayslimit:
                    print(f"Reached maximum iterations: {dayslimit}")
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



