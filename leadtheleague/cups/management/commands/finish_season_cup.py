from cups.models import SeasonCup
from cups.utils.update_cup_season import set_season_cup_winner, set_season_cup_completed
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Marks a SeasonCup as completed and sets the winner."

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            type=int,
            help="Year of the season to process. If omitted, processes all seasons.",
        )

    def handle(self, *args, **options):
        season_year = options.get("season")
        season_cups = SeasonCup.objects.all()

        # Филтрираме по зададена година, ако е предоставена
        if season_year:
            season_cups = season_cups.filter(season__year=season_year)

        if not season_cups.exists():
            self.stdout.write(
                self.style.WARNING(f"No SeasonCup records found for season {season_year or 'all seasons'}.")
            )
            return

        for season_cup in season_cups:
            if season_cup.is_completed:
                self.stdout.write(self.style.WARNING(f"{season_cup} is already completed. Skipping."))
                continue

            try:
                self.stdout.write(f"Processing {season_cup}...")
                set_season_cup_winner(season_cup)
                set_season_cup_completed(season_cup)
                self.stdout.write(self.style.SUCCESS(f"SeasonCup {season_cup} completed. Winner: {season_cup.champion_team.name}."))
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Error processing {season_cup}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error for {season_cup}: {e}"))