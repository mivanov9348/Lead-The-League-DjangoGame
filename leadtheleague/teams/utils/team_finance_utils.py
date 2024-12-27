from decimal import Decimal
from django.db import transaction
from finance.utils.bank_utils import get_bank, distribute_income
from game.utils.get_season_stats_utils import get_current_season
from teams.models import TeamFinance, TeamTransaction

def get_team_finance_overview(team):
    try:
        finance = TeamFinance.objects.get(team=team)
        return {
            "balance": finance.balance,
            "total_income": finance.total_income,
            "total_expenses": finance.total_expenses,
        }
    except TeamFinance.DoesNotExist:
        return {
            "balance": Decimal('0.00'),
            "total_income": Decimal('0.00'),
            "total_expenses": Decimal('0.00'),
        }

def get_recent_team_transactions(team, limit=5):
    return TeamTransaction.objects.filter(team=team).order_by('-created_at')[:limit]

def check_team_balance(team, amount_needed):
    try:
        team_finance = TeamFinance.objects.get(team=team)
        return team_finance.balance >= Decimal(amount_needed)
    except TeamFinance.DoesNotExist:
        return False

def process_bank_tax(team, income, description):
    tax_percentage = Decimal("0.2")
    tax_amount = Decimal(income) * tax_percentage

    with transaction.atomic():
        team_expense(team, tax_amount, f'Tax deduction: {description}')

        bank = get_bank()
        distribute_income(bank, tax_amount, description, team)


def team_match_profit(team, match, income, description):
    if income <= 0:
        raise ValueError("Income amount must be positive!")

    with transaction.atomic():
        # Step 1: Record the full income
        team_income(team, income, f'Income from {match.home_team} - {match.away_team} (attendance: {match.attendance})')

        # Step 2: Process the tax
        process_bank_tax(team, income, description)

def sell_player_income(team, player, amount):
    if amount <= 0:
        raise ValueError("The sale amount must be positive.")

    description = f"{team.name} buy {player.name}."

    with transaction.atomic():
        team_income(team, amount, description)

        process_bank_tax(team, amount, description)

def buy_player_expense(team, player, amount):
    if amount <= 0:
        raise ValueError("The purchase amount must be positive.")

    description = f"Expense for the purchase of {player.name}."

    with transaction.atomic():
        team_expense(team, amount, description)

        process_bank_tax(team, amount, description)

def team_transaction(team, amount, transaction_type, description=None):
    if amount <= 0:
        raise ValueError("Transaction amount must be positive!")
    season = get_current_season()
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
                description=description,
                season=season
            )

    except TeamFinance.DoesNotExist:
        raise ValueError(f"The team {team.name} does not have a finance wallet!")


def team_income(team, amount, description):
    team_transaction(team, amount, 'IN', description)


def team_expense(team, price, description):
    team_transaction(team, price, 'OUT', description)


def get_team_transactions(team):
    return team.team_transactions.order_by('-created_at')
