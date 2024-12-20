from django.core.management import BaseCommand
from europeancups.utils.group_stage_utils import simulate_matchday_matches, update_euro_cup_standings
from game.utils.schedule_utils import get_next_euro_match_day

class Command(BaseCommand):
    help = 'Simulates all group stage matches for European Cups.'

    def handle(self, *args, **options):
        next_match_day = get_next_euro_match_day()

        if next_match_day:
            simulate_matchday_matches(next_match_day)
            update_euro_cup_standings(next_match_day)
            self.stdout.write(self.style.SUCCESS(f'Successfully simulated matches and updated standings for {next_match_day}.'))
        else:
            self.stdout.write(self.style.WARNING('No upcoming European match days found.'))
