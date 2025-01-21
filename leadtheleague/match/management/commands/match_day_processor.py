from django.core.management.base import BaseCommand

from game.models import MatchSchedule
from leagues.utils import auto_set_league_champions
from match.models import Match
from match.utils.match.processing import match_day_processor
from match.utils.match.stats import generate_players_match_stats
from players.utils.get_player_stats_utils import ensure_all_teams_has_minimum_players
from staff.utils.agent_utils import scouting_new_talents, generate_agents
from teams.utils.lineup_utils import ensure_team_tactics


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
            dayslimit = 1
            for i, match_day in enumerate(match_days):
                if i >= dayslimit:
                    print(f"Reached maximum iterations: {dayslimit}")
                    break

                print(f"Processing match day {i + 1}/{dayslimit}: {match_day.date}")
                match_day_processor(match_day.date)

        except:
            print('Error when processing')
    # auto_set_league_champions()
