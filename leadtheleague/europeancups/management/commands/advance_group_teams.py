from django.core.management.base import BaseCommand
from django.db.models import Max

from europeancups.models import EuropeanCupSeason
from europeancups.utils.group_stage_utils import advance_teams_from_groups


class Command(BaseCommand):
    help = 'Advances teams from group stage to knockout stage for the only European Cup.'

    def handle(self, *args, **options):
        try:
            european_cup_season = EuropeanCupSeason.objects.annotate(
                latest_season=Max('season__year')
            ).order_by('-latest_season').first()

            if not european_cup_season:
                self.stdout.write(self.style.ERROR("No European Cup Season found."))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error finding European Cup Season: {str(e)}"))
            return

        advancing_teams, eliminated_teams = advance_teams_from_groups(european_cup_season)

        self.stdout.write(
            self.style.SUCCESS(f"Teams advancing from {european_cup_season.cup.name} ({european_cup_season.season}):"))
        for team in advancing_teams:
            self.stdout.write(f" - {team}")

        self.stdout.write(
            self.style.WARNING(f"Teams eliminated from {european_cup_season.cup.name} ({european_cup_season.season}):"))
        for team in eliminated_teams:
            self.stdout.write(f" - {team}")
