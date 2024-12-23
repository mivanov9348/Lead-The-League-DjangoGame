import random
from django.core.management.base import BaseCommand
from cups.utils.update_cup_season import update_winner
from fixtures.models import CupFixture
from game.models import MatchSchedule


class Command(BaseCommand):
    help = 'Generate random results for the last unfinished round of CupFixtures'

    def handle(self, *args, **kwargs):
        last_unfinished_round = (
            CupFixture.objects.filter(is_finished=False)
            .order_by('-round_number')
            .first()
        )

        if not last_unfinished_round:
            self.stdout.write(self.style.WARNING("No unfinished CupFixtures found."))
            return

        round_number = last_unfinished_round.round_number

        fixtures = CupFixture.objects.filter(round_number=round_number, is_finished=False)

        if not fixtures.exists():
            self.stdout.write(self.style.WARNING("No fixtures found for the last round."))
            return

        match_dates = set()

        self.stdout.write(f"Generating results for round {round_number} with {fixtures.count()} fixtures...")

        for fixture in fixtures:
            home_goals = random.randint(0, 5)
            away_goals = random.randint(0, 5)

            while home_goals == away_goals:
                home_goals = random.randint(0, 5)
                away_goals = random.randint(0, 5)

            fixture.home_goals = home_goals
            fixture.away_goals = away_goals
            fixture.is_finished = True
            fixture.save()
            update_winner(fixture)
            self.stdout.write(
                f"Fixture {fixture}: {fixture.home_team} {home_goals} - {away_goals} {fixture.away_team}"
            )
            match_dates.add(fixture.date)

        MatchSchedule.objects.filter(date__in=match_dates, event_type='cup').update(is_played=True)

        self.stdout.write(self.style.SUCCESS(f"All fixtures for round {round_number} have been updated."))
