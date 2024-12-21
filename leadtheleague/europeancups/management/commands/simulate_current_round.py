from django.core.management.base import BaseCommand
from europeancups.models import EuropeanCupSeason
from europeancups.utils.knockout_utils import simulate_euro_knockout_round

class Command(BaseCommand):
    help = 'Simulates the latest European knockout round and progresses to the next stage.'

    def handle(self, *args, **options):
        try:
            european_cup_season = EuropeanCupSeason.objects.first()
            if not european_cup_season:
                self.stdout.write(self.style.ERROR("No active European Cup season found."))
                return

            # Find the last unplayed knockout stage
            last_knockout_stage = european_cup_season.knockout_stages.filter(is_played=False).order_by(
                'stage_order').first()

            if not last_knockout_stage:
                self.stdout.write(self.style.ERROR("No unplayed European knockout stage found."))
                return

            advancing_teams = simulate_euro_knockout_round(
                european_cup_season=european_cup_season,
                knockout_stage=last_knockout_stage)


            self.stdout.write(self.style.SUCCESS(
                f"Knockout stage '{last_knockout_stage.stage_name}' simulated successfully."
            ))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
