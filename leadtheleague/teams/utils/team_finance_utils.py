from decimal import Decimal
from django.db import transaction
from finance.utils.bank_utils import get_bank, distribute_income
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

    team_finance = TeamFinance.objects.filter(team=team).first()
    if not team_finance:
        return

    bank = get_bank()

    create_transaction(bank, 'IN', team_finance.balance, f'Terminate Team ({team.name})')
    team_finance.delete()


def team_match_profit(team, income, description):
    if income <= 0:
        raise ValueError("Income amount must be positive!")

    tax_percentage = Decimal("0.2")
    team_percentage = Decimal("0.8")

    tax_amount = income * float(tax_percentage)
    team_amount = income * float(tax_percentage)

    with transaction.atomic():
        team_income(team, team_amount)
        bank = get_bank()
        distribute_income(bank, tax_amount, description)

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
