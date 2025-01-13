from django.core.management.base import BaseCommand
from match.utils.match.processing import match_day_processor

class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            match_day_processor('2025-03-23')
            match_day_processor('2025-03-24')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
