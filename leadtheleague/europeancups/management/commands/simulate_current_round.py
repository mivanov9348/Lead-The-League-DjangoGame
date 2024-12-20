from django.core.management.base import BaseCommand
from europeancups.models import EuropeanCupSeason
from europeancups.utils.knockout_utils import simulate_euro_knockout_round
from game.models import MatchSchedule


class Command(BaseCommand):
    help = 'Simulates the latest European knockout round and progresses to the next stage.'

    def handle(self, *args, **options):
        try:
            european_cup_season = EuropeanCupSeason.objects.first()
            if not european_cup_season:
                self.stdout.write(self.style.ERROR("No active European Cup season found."))
                return

            last_schedule = MatchSchedule.objects.filter(
                season=european_cup_season.season,
                event_type='euro',
                is_played=False
            ).order_by('date').first()

            if not last_schedule:
                self.stdout.write(self.style.ERROR("No unplayed European knockout round found."))
                return

            advancing_teams, new_knockout_stage = simulate_euro_knockout_round(
                european_cup_season=european_cup_season,
                match_date=last_schedule.date
            )

            last_schedule.is_played = True
            last_schedule.save()

            self.stdout.write(self.style.SUCCESS(
                f"Knockout round for {last_schedule.date} simulated successfully. "
                f"Next stage '{new_knockout_stage.stage_name}' created."
            ))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
