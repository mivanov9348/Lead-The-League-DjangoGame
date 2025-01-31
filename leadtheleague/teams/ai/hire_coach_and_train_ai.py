from django.utils import timezone
from datetime import datetime

from django.db import transaction
from django.db.models import F
from finance.models import Bank
from finance.utils.bank_utils import distribute_income
from game.utils.get_season_stats_utils import get_current_season
from messaging.utils.category_messages_utils import create_new_coach_message
from players.models import PositionAttribute
from staff.models import Coach
from teams.models import TeamPlayer, Team, TeamFinance, TrainingImpact
from teams.utils.team_finance_utils import team_expense
from teams.utils.training_utils import player_training


def ai_manage_coaches_and_training():
    print("Starting AI process for coach assignment and training...")
    teams = Team.objects.filter(user__isnull=True).select_related('teamfinance')

    for team in teams:
        print(f"Processing team: {team.name}")

        # Назначаване на треньор (ако няма)
        if not Coach.objects.filter(team=team).exists():
            ai_assign_coach(team)

        # Трениране на играчите (ако има треньор)
        ai_train_players(team)

    print("AI coach assignment and training process completed.")


def ai_assign_coach(team):
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
                print(
                    f"{team.name} does not have enough balance for this transaction! Current balance: {team_finance.balance}, required: {coach.price}.")
                return False

            coach.team = team
            coach.save()

            team_finance.balance -= coach.price
            team_finance.save()

            team_expense(team, coach.price, f'{team.name} assign coach {coach.first_name} {coach.last_name}')
            create_new_coach_message(coach, team)
            bank = Bank.objects.get(is_main=True)
            distribute_income(bank, coach.price, f"{team} hire coach {coach.first_name} {coach.last_name}", team)

            print(f"{team.name} hired coach {coach.first_name} {coach.last_name}.")
            return True

    except Exception as e:
        print(f"Unexpected error during transaction: {e}")
        return False


def get_training_attribute_for_player(player):
    position_attributes = PositionAttribute.objects.filter(position=player.position).order_by('-importance')
    if position_attributes.exists():
        return position_attributes.first().attribute
    return None


def ai_train_players(team):
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

        attribute = get_training_attribute_for_player(player)
        if not attribute:
            print(f"No training attribute found for {player.first_name} {player.last_name}.")
            continue

        training_result = player_training(coach, player)
        training_impact = training_result["training_impact"]

        setattr(player, attribute.name, F(attribute.name) + training_impact)
        player.save()

        TrainingImpact.objects.create(
            player=player,
            coach=coach,
            training_impact=training_impact,
            notes=f"Trained {attribute.name} with impact {training_impact}",
            date=timezone.now()
        )

        print(f"Trained {player.first_name} {player.last_name} in {attribute.name} with impact {training_impact}.")
