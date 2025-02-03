import random
from django.db import transaction
from messaging.utils.category_messages_utils import update_stadium_message
from stadium.utils.get_stadium_stats import get_next_stadium_tier
from stadium.utils.stadium_upgrade_utils import upgrade_stadium
from teams.models import Team
from teams.utils.team_finance_utils import team_expense, check_team_balance


class StadiumAI:
    @staticmethod
    def upgrade_stadiums():
        print("Stadium AI: Starting stadium upgrade evaluation...")
        teams = Team.objects.filter(user__isnull=True).select_related("stadium")

        for team in teams:
            print(f"Processing team: {team.name}")
            stadium = team.stadium
            if not stadium:
                print(f"{team.name} does not have a stadium. Skipping...")
                continue

            next_tier = get_next_stadium_tier(stadium.tier)
            if not next_tier:
                print(f"{team.name}: No higher stadium tier available.")
                continue

            if not check_team_balance(team, next_tier.upgrade_cost):
                print(f"{team.name}: Not enough balance for upgrade ({next_tier.upgrade_cost}).")
                continue

            if StadiumAI.should_upgrade(team, stadium, next_tier):
                StadiumAI.perform_upgrade(team, stadium, next_tier)
            else:
                print(f"{team.name}: Decided not to upgrade the stadium.")

        print("Stadium AI: Stadium upgrade evaluation completed.")

    @staticmethod
    def should_upgrade(team, stadium, next_tier):
        financial_status = float(team.teamfinance.balance) if hasattr(team, 'teamfinance') else 0.0
        popularity_factor = team.reputation if hasattr(team, 'reputation') else 0

        upgrade_chance = min(90, 30 + (financial_status / 1_000_000.0) + (popularity_factor / 10))

        return random.randint(1, 100) <= upgrade_chance

    @staticmethod
    @transaction.atomic
    def perform_upgrade(team, stadium, next_tier):
        print(f"Upgrading stadium for {team.name} to {next_tier.name}...")
        team_expense(team, next_tier.upgrade_cost, f"Upgraded stadium to {next_tier.name}")
        upgrade_stadium(stadium, next_tier)
        update_stadium_message(team, stadium.name, next_tier.name)
        print(f"{team.name}: Stadium successfully upgraded to {next_tier.name}!")
