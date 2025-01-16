from django.core.management.base import BaseCommand

from finance.utils.prize_utils import calculate_team_percentages
from match.utils.match.processing import match_day_processor


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            # match_day_processor('2025-03-13')
            # match_day_processor('2025-03-14')
            # match_day_processor('2025-03-15')
            # match_day_processor('2025-03-16')
            # match_day_processor('2025-03-17')

            result = calculate_team_percentages(30)
            print(result)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
