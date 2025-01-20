from django.core.management.base import BaseCommand

from game.models import MatchSchedule
from leagues.utils import auto_set_league_champions
from match.models import Match
from match.utils.match.processing import match_day_processor
from staff.utils.agent_utils import scouting_new_talents, generate_agents


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")

        match_day_processor("2025-04-21")


        # match_days = MatchSchedule.objects.filter(event_type='euro', is_played=False).order_by('date')
        # print(match_days)
        # # try:
        # #     for match_day in match_days:
        # #         match_day_processor(match_day.date)
        # #
        # # except:
        # #     print('Error when processing')
        #
        # # match_days = MatchSchedule.objects.filter(event_type='cup', is_played=False).order_by('date')
        # #
        # # try:
        # #     for match_day in match_days:
        # #         match_day_processor(match_day.date)
        # #
        # # except:
        # #     print('Error when processing')

        # match_days = MatchSchedule.objects.filter(event_type='league', is_played=False).order_by('date')
        # try:
        #     dayslimit = 5
        #     for i, match_day in enumerate(match_days):
        #         if i >= dayslimit:
        #             print(f"Reached maximum iterations: {dayslimit}")
        #             break
        #
        #         print(f"Processing match day {i + 1}/{dayslimit}: {match_day.date}")
        #         match_day_processor(match_day.date)
        #
        # except:
        #     print('Error when processing')

        # auto_set_league_champions()

