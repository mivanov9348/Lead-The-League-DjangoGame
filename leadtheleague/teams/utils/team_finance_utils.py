from decimal import Decimal
from django.db import transaction
from finance.utils.bank_utils import get_bank
from finance.utils.transaction_utils import create_transaction
from teams.models import TeamFinance

def check_team_balance(team, amount_needed):
    try:
        team_finance = TeamFinance.objects.get(team=team)
        return team_finance.balance >= Decimal(amount_needed)
    except TeamFinance.DoesNotExist:
        return False

@transaction.atomic
def terminate_team_finance(team):
    print(f"Започваме процеса на прекратяване на финанси за отбор {team.name}")

    team_finance = TeamFinance.objects.filter(team=team).first()
    if not team_finance:
        print(f"Отборът {team.name} не разполага с финансови данни.")
        return

    bank = get_bank()
    print(f"Getting Bank Information: {bank}")

    create_transaction(bank, 'IN', team_finance.balance, f'Terminate Team ({team.name})')
    print(f"Създадена транзакция за прекратяване на отбор ({team.name}) с баланс {team_finance.balance}")

    team_finance.delete()
    print(f"Финансовите данни за отбор {team.name} бяха успешно изтрити.")

def team_income(team, amount):
    try:
        with transaction.atomic():
            team_finance = TeamFinance.objects.get(team=team)
            amount_decimal = Decimal(amount)
            team_finance.balance += amount_decimal
            team_finance.total_income += amount_decimal
            team_finance.save()
    except TeamFinance.DoesNotExist:
        raise ValueError(f"The teams {team.name} does not have a finance wallet!")


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
