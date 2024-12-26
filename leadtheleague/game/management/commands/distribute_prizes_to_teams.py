from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finance.utils.prize_utils import distribute_league_fund, distribute_global_fund, distribute_match_fund, \
    distribute_cup_fund
from game.models import Season
from game.utils.get_season_stats_utils import get_current_season


class Command(BaseCommand):
    help = "Разпределя наградите от фондовете (League, Cup, Global, Match) за текущия сезон"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        season = get_current_season()

        try:
            # Разпределение на фондовете
            distribute_league_fund(season)
            self.stdout.write("League Fund успешно разпределен.")

            distribute_cup_fund(season)
            self.stdout.write("Cup Fund успешно разпределен.")

            distribute_global_fund()
            self.stdout.write("Global Fund успешно разпределен.")

            distribute_match_fund(season)
            self.stdout.write("Match Fund успешно разпределен.")

            self.stdout.write(self.style.SUCCESS("Всички фондове бяха успешно разпределени!"))

        except Exception as e:
            raise CommandError(f"Грешка при разпределението: {e}")
