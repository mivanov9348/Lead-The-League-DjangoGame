from django.core.management.base import BaseCommand
from match.utils.match_day_processor import match_day_processor

class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            match_day_processor('2025-01-23')
            match_day_processor('2025-01-25')
            match_day_processor('2025-01-28')
            match_day_processor('2025-01-30')
            match_day_processor('2025-01-31')


        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
