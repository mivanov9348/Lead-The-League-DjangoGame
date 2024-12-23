from django.core.management import BaseCommand
from game.utils.get_season_stats_utils import get_current_season
from leagues.utils import assign_league_champions

class Command(BaseCommand):
    help = "Completes the league seasons and assigns champions."
    def handle(self, *args, **kwargs):
        season = get_current_season()
        assign_league_champions(season)


