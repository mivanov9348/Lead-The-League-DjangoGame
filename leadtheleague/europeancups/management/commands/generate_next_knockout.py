from django.core.management.base import BaseCommand
from europeancups.models import EuropeanCupSeason
from game.models import MatchSchedule
from europeancups.utils.knockout_utils import generate_euro_cup_knockout


class Command(BaseCommand):
    help = "Generates knockout fixtures for all active EuropeanCupSeason instances in the current season."

    def handle(self, *args, **options):
        european_cup_seasons = EuropeanCupSeason.objects.filter(season__is_active=True)

        if not european_cup_seasons.exists():
            self.stdout.write(self.style.ERROR("No active European Cup seasons found."))
            return

        for european_cup_season in european_cup_seasons:
            self.stdout.write(f"Processing EuropeanCupSeason: {european_cup_season}")

            free_date = MatchSchedule.objects.filter(
                season=european_cup_season.season,
                event_type='euro',
                is_euro_cup_day_assigned=False,
                is_played=False
            ).order_by('date').first()

            if not free_date:
                self.stdout.write(self.style.ERROR(f"No available date for EuropeanCupSeason {european_cup_season}."))
                continue

            generate_euro_cup_knockout(european_cup_season, free_date.date)

            free_date.is_euro_cup_day_assigned = True
            free_date.save()

            self.stdout.write(self.style.SUCCESS(
                f"Knockout fixtures generated for EuropeanCupSeason {european_cup_season} on date {free_date.date}."))
