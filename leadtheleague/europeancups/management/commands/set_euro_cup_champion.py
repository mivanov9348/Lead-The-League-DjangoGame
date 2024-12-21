from django.core.management.base import BaseCommand
from europeancups.models import EuropeanCupSeason
from europeancups.utils.euro_cup_season_utils import set_european_cup_season_champion


class Command(BaseCommand):
    help = 'Set the champion for the current European Cup season based on the final match.'

    def handle(self, *args, **kwargs):
        try:
            champion = set_european_cup_season_champion()
            self.stdout.write(self.style.SUCCESS(f"The champion for the current European Cup season is set to {champion.name}."))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
