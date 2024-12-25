from decimal import Decimal
from django.db import transaction
from finance.utils.bank_utils import get_bank, distribute_income
from teams.models import TeamFinance, TeamTransaction

def check_team_balance(team, amount_needed):
    try:
        team_finance = TeamFinance.objects.get(team=team)
        return team_finance.balance >= Decimal(amount_needed)
    except TeamFinance.DoesNotExist:
        return False


def team_match_profit(team, income, description):
    if income <= 0:
        raise ValueError("Income amount must be positive!")

    tax_percentage = Decimal("0.2")
    team_percentage = Decimal("0.8")

    tax_amount = income * float(tax_percentage)
    team_amount = income * float(tax_percentage)

    with transaction.atomic():
        team_income(team, team_amount, 'Income from Match')
        bank = get_bank()
        distribute_income(bank, tax_amount, description, team)

def team_transaction(team, amount, transaction_type, description=None):
    if amount <= 0:
        raise ValueError("Transaction amount must be positive!")

    bank = get_bank()

    try:
        with transaction.atomic():
            team_finance = TeamFinance.objects.get(team=team)
            amount_decimal = Decimal(amount)

            if transaction_type == 'IN':
                team_finance.balance += amount_decimal
                team_finance.total_income += amount_decimal
            elif transaction_type == 'OUT':
                if team_finance.balance < amount_decimal:
                    raise ValueError(f"{team.name} does not have enough balance for this transaction!")
                team_finance.balance -= amount_decimal
                team_finance.total_expenses += amount_decimal
            else:
                raise ValueError("Invalid transaction type! Use 'IN' or 'OUT'.")

            team_finance.save()

            TeamTransaction.objects.create(
                team=team,
                bank=bank,
                type=transaction_type,
                amount=amount_decimal,
                description=description
            )

    except TeamFinance.DoesNotExist:
        raise ValueError(f"The team {team.name} does not have a finance wallet!")

def team_income(team, amount, description):
    team_transaction(team, amount, 'IN', description)

def team_expense(team, price,description):
    team_transaction(team, price, 'OUT', description)


def get_team_transactions(team):
        return team.team_transactions.order_by('-created_at')
