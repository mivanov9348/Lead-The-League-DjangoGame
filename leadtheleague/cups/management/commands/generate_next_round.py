from django.core.management.base import BaseCommand
from cups.models import SeasonCup
from cups.utils.generate_cup_fixtures import generate_next_round_fixtures
from cups.utils.update_cup_season import populate_progressing_team
from game.models import MatchSchedule, Season

class Command(BaseCommand):
    help = "Generate the next round fixtures for all SeasonCups in a season."

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            type=int,
            help="Year of the season to process. If omitted, processes all seasons.",
        )

    def handle(self, *args, **options):
        season_year = options.get("season")
        season_cups = SeasonCup.objects.all()

        if season_year:
            season_cups = season_cups.filter(season__year=season_year)

        if not season_cups.exists():
            self.stdout.write(
                self.style.WARNING(f"No SeasonCup records found for season {season_year or 'all seasons'}."))
            return

        next_available_date = MatchSchedule.objects.filter(
            season__in=Season.objects.filter(year=season_year) if season_year else Season.objects.all(),
            event_type='cup',
            is_cup_day_assigned=False,
        ).order_by('date').first()

        if not next_available_date:
            self.stdout.write(self.style.ERROR("No available dates for generating fixtures."))
            return

        self.stdout.write(f"Using shared date: {next_available_date.date}")

        for season_cup in season_cups:
            try:
                self.stdout.write(f"Processing {season_cup.cup.name} ({season_cup.season.year})...")
                populate_progressing_team(season_cup)
                generate_next_round_fixtures(season_cup, next_available_date)
                next_available_date.is_cup_day_assigned = True
                next_available_date.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Next round fixtures generated successfully for {season_cup.cup.name}!"))
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Error processing {season_cup.cup.name}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error for {season_cup.cup.name}: {e}"))
