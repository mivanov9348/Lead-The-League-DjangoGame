from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import F

from finance.models import Transaction
from finance.utils.bank_utils import get_bank, distribute_income
from game.utils.get_season_stats_utils import get_current_season
from teams.models import TeamFinance, TeamTransaction, Team


def get_recent_team_transactions(team, limit=5):
    return TeamTransaction.objects.filter(team=team).order_by('-created_at')[:limit]


def get_teams_by_balance(limit=None):
    teams = Team.objects.filter(is_active=True) \
        .annotate(
        current_balance=F('teamfinance__balance')
    ) \
        .order_by('-current_balance')

    if limit:
        teams = teams[:limit]
    return teams


def check_team_balance(team, amount_needed):
    try:
        team_finance = TeamFinance.objects.get(team=team)
        print(f"Balance: {team_finance.balance}, Needed: {amount_needed}")
        return team_finance.balance >= Decimal(amount_needed)
    except TeamFinance.DoesNotExist:
        print("TeamFinance entry does not exist.")
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
        team_income(team, income, f'Income from {match.home_team} - {match.away_team} (attendance: {match.attendance})')

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
    # Проверка на входните данни
    if amount is None:
        raise ValueError("Transaction amount cannot be None!")
    try:
        amount_decimal = Decimal(amount)
        if amount_decimal <= 0:
            raise ValueError("Transaction amount must be positive!")
    except InvalidOperation:
        raise ValueError(f"Invalid transaction amount: {amount}")

    print(f"Processing transaction: team={team.name}, amount={amount_decimal}, type={transaction_type}, description={description}")

    season = get_current_season()
    bank = get_bank()
    print(f"Current season: {season}, Bank: {bank}")

    try:
        with transaction.atomic():
            team_finance = TeamFinance.objects.get(team=team)
            print(f"Team finance found: {team_finance}")

            if transaction_type == 'IN':
                team_finance.balance += amount_decimal
                team_finance.total_income += amount_decimal
                bank.balance += amount_decimal
                bank.total_income += amount_decimal
                print(f"Income transaction processed: new team balance={team_finance.balance}, bank balance={bank.balance}")
            elif transaction_type == 'OUT':
                if team_finance.balance < amount_decimal:
                    raise ValueError(f"{team.name} does not have enough balance for this transaction! Current balance: {team_finance.balance}, required: {amount_decimal}")
                team_finance.balance -= amount_decimal
                team_finance.total_expenses += amount_decimal
                bank.balance -= amount_decimal
                bank.total_expenses += amount_decimal
                print(f"Expense transaction processed: new team balance={team_finance.balance}, bank balance={bank.balance}")
            else:
                raise ValueError("Invalid transaction type! Use 'IN' or 'OUT'.")

            team_finance.save()
            bank.save()
            print(f"Team finance and bank updated and saved.")

            TeamTransaction.objects.create(
                team=team,
                bank=bank,
                type=transaction_type,
                amount=amount_decimal,
                description=description,
                season=season
            )
            print(f"Transaction record created: amount={amount_decimal}, type={transaction_type}, description={description}")

    except TeamFinance.DoesNotExist:
        print(f"Finance wallet not found for team: {team.name}")
        raise ValueError(f"The team {team.name} does not have a finance wallet!")

    except Exception as e:
        print(f"Unexpected error during transaction: {e}")
        raise



def team_income(team, amount, description):
    team_transaction(team, amount, 'IN', description)

def team_expense(team, price, description):
    team_transaction(team, price, 'OUT', description)


def get_team_transactions(team):
    return team.team_transactions.order_by('-created_at')
