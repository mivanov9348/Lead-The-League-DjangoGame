from decimal import Decimal
from django.db import transaction
from teams.models import TeamFinance

@transaction.atomic
def create_team_finance(team):
    initial_balance = 1000000.0  # Начален баланс

    # Проверка дали отборът вече има финансов профил
    if hasattr(team, 'finance'):
        raise ValueError(f'The team {team.name} already has finance profile!')

    # Създаване на финансова инстанция
    team_finance = TeamFinance.objects.create(
        team=team,
        balance=initial_balance,
        total_income=0.0,
        total_expenses=0.0
    )

    return team_finance


def team_income(team, price):
    try:
        with transaction.atomic():
            teamFinance = TeamFinance.objects.get(team=team)
            price_decimal = Decimal(price)
            teamFinance.balance += price_decimal
            teamFinance.total_income += price_decimal
            teamFinance.save()
    except TeamFinance.DoesNotExist:
        raise ValueError("Team have not Finance Wallet!")


def team_expense(team, price):
    try:
        with transaction.atomic():
            teamFinance = TeamFinance.objects.get(team=team)
            price_decimal = Decimal(price)
            teamFinance.balance -= price_decimal
            teamFinance.total_expenses += price_decimal
            teamFinance.save()
    except TeamFinance.DoesNotExist:
        raise ValueError("Team have not Finance Wallet!")