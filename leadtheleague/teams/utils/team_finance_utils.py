from decimal import Decimal
from django.db import transaction
from finance.utils.bank_utils import get_bank
from finance.utils.transaction_utils import create_transaction
from teams.models import TeamFinance

@transaction.atomic
def terminate_team_finance(team):
    print(f"Започваме процеса на прекратяване на финанси за отбор {team.name}")

    # Проверяваме направо дали има свързани финансови данни
    team_finance = TeamFinance.objects.filter(team=team).first()
    if not team_finance:
        print(f"Отборът {team.name} не разполага с финансови данни.")
        return

    print(f"Намерихме финансова информация за отбор {team.name} с баланс {team_finance.balance}")

    bank = get_bank()
    print(f"Извличаме банкова информация: {bank}")

    create_transaction(bank, 'IN', team_finance.balance, f'Terminate Team ({team.name})')
    print(f"Създадена транзакция за прекратяване на отбор ({team.name}) с баланс {team_finance.balance}")

    team_finance.delete()
    print(f"Финансовите данни за отбор {team.name} бяха успешно изтрити.")

@transaction.atomic
def create_team_finance(team):
    # Проверка дали отборът вече има финансов профил
    if hasattr(team, 'finance'):
        raise ValueError(f'The team {team.name} already has finance profile!')

    # THIS MUST BE TAKEN FROM SETTINGS
    new_team_balance_prize = 2000000

    bank = get_bank()
    create_transaction(bank, 'OUT', new_team_balance_prize, f'Team Initial Balance ({team})')

    team_finance = TeamFinance.objects.create(
        team=team,
        balance=0.0,
        total_income=0.0,
        total_expenses=0.0
    )

    team_income(team, new_team_balance_prize)

    return team_finance

def team_income(team, amount):
    try:
        with transaction.atomic():
            team_finance = TeamFinance.objects.get(team=team)
            amount_decimal = Decimal(amount)
            team_finance.balance += amount_decimal
            team_finance.total_income += amount_decimal
            team_finance.save()
    except TeamFinance.DoesNotExist:
        raise ValueError(f"The team {team.name} does not have a finance wallet!")

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
