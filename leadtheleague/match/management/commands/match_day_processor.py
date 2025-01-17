from django.core.management.base import BaseCommand

from cups.utils.generate_cup_fixtures import process_all_season_cups, populate_season_cups_with_teams
from finance.utils.prize_utils import calculate_team_percentages, end_of_season_fund_distribution
from fixtures.utils import generate_all_league_fixtures
from game.utils.get_season_stats_utils import get_previous_season, get_current_season
from leagues.utils import populate_teams_for_season
from match.utils.match.generator import generate_cup_matches, generate_league_matches
from match.utils.match.processing import match_day_processor


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            match_day_processor('2025-01-19')


        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
