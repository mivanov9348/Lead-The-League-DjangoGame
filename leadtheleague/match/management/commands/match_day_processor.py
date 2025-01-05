from django.core.management.base import BaseCommand
from match.utils.match_day_processor import match_day_processor
from match.utils.match_helpers import get_random_match_event, calculate_event_success_rate, get_event_result, \
    get_event_template
from players.models import Player


class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            match_day_processor('2025-01-30')
            # player = Player.objects.first()
            # print(player)
            # event = get_random_match_event()
            # print(event)
            # success = calculate_event_success_rate(event, player)
            # print(success)
            # event_result = get_event_result(event, success)
            # print(event_result)
            # template = get_event_template(event_result)
            # print(template)


        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
