from django.core.management.base import BaseCommand
from django.db import transaction
from game.models import MatchSchedule
from leagues.utils import simulate_day_league_fixtures


class Command(BaseCommand):
    help = 'Simulate league matches and update standings'

    def handle(self, *args, **kwargs):
        match_schedule = MatchSchedule.objects.filter(
            event_type='league', is_played=False
        ).order_by('date').first()

        if not match_schedule:
            self.stdout.write(self.style.WARNING('No league matches left to simulate.'))
            return

        match_date = match_schedule.date

        simulate_day_league_fixtures(match_date)

        match_schedule.is_played = True
        match_schedule.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully simulated league matches for {match_date}'))