from django.db import transaction
from django.utils import timezone
from django.db.models import F
from game.utils.get_season_stats_utils import get_current_season
from players.models import PositionAttribute
from staff.models import Coach
from teams.models import TeamFinance, TrainingImpact, TeamPlayer


class CoachAI:
    @staticmethod
    def manage_coaches_and_training(team):
        print(f"Processing coach and training for: {team.name}")

        if not Coach.objects.filter(team=team).exists():
            if not CoachAI.assign_coach(team):
                print(f"{team.name}: No coach assigned.")
                return

        CoachAI.train_players(team)

    @staticmethod
    def assign_coach(team):
        if Coach.objects.filter(team=team).exists():
            print(f"{team.name} already has a coach.")
            return False

        if team.teamfinance.balance <= 0:
            print(f"{team.name} has no budget to hire a coach.")
            return False

        available_coaches = Coach.objects.filter(team__isnull=True, price__lte=team.teamfinance.balance)
        if not available_coaches.exists():
            print(f"No available coaches within budget for {team.name}.")
            return False

        coach = available_coaches.order_by('-rating').first()

        try:
            with transaction.atomic():
                team_finance = TeamFinance.objects.select_for_update().get(team=team)

                if team_finance.balance < coach.price:
                    print(f"{team.name} does not have enough balance for this transaction!")
                    return False

                coach.team = team
                coach.save()

                team_finance.balance -= coach.price
                team_finance.save()

                print(f"{team.name} hired coach {coach.first_name} {coach.last_name}.")
                return True

        except Exception as e:
            print(f"Unexpected error during transaction: {e}")
            return False

    @staticmethod
    def train_players(team):
        coach = Coach.objects.filter(team=team).first()
        if not coach:
            print(f"{team.name} has no coach. Skipping training.")
            return

        current_season = get_current_season()
        current_date = current_season.current_date

        if TrainingImpact.objects.filter(coach=coach, date__date=current_date).exists():
            print(f"{team.name} has already trained today. Skipping training.")
            return

        players = TeamPlayer.objects.filter(team=team).select_related('player')

        for team_player in players:
            player = team_player.player

            if TrainingImpact.objects.filter(player=player, coach=coach, date__date=current_date).exists():
                print(f"{player.first_name} {player.last_name} has already been trained today.")
                continue

            attribute = PositionAttribute.objects.filter(position=player.position).order_by('-importance').first()
            if not attribute:
                print(f"No training attribute found for {player.first_name} {player.last_name}.")
                continue

            training_impact = 1

            training_attribute_name = attribute.attribute.name
            setattr(player, training_attribute_name, F(training_attribute_name) + training_impact)
            player.save()

            TrainingImpact.objects.create(
                player=player,
                coach=coach,
                training_impact=training_impact,
                notes=f"Trained {attribute.attribute.name} with impact {training_impact}",
                date=timezone.now()
            )

            print(f"Trained {player.first_name} {player.last_name} in {attribute.attribute.name} with impact {training_impact}.")
