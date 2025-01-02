from django.core.management.base import BaseCommand
from players.utils.player_analytics_utils import update_season_analytics, export_to_csv, panda_analyze


class Command(BaseCommand):
    help = 'Update season analytics'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write('Starting season analytics update...')
            # export_to_csv()
            # panda_analyze()
            update_season_analytics()
            self.stdout.write(self.style.SUCCESS('Season analytics updated successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {e}'))
