from django.core.management.base import BaseCommand

from europeancups.utils.euro_cup_season_utils import get_current_knockout_stage_order, get_current_european_cup_season, \
    finalize_euro_cup
from game.models import MatchSchedule
from match.utils.match.processing import match_day_processor
from teams.models import Team


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            # match_day_processor('2025-04-04')
            current_euro_season = get_current_european_cup_season()
            current_stage_order = get_current_knockout_stage_order(current_euro_season)
            winner_team = Team.objects.filter(id=9702).first()

            if current_stage_order.is_final:
                finalize_euro_cup(current_euro_season, winner_team)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
