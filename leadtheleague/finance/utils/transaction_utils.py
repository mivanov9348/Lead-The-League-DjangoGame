from django.db import transaction
from django.db.models import Sum
from finance.models import Transaction
from game.utils.get_season_stats_utils import get_current_season


def get_transactions_for_bank(bank):
    return bank.transactions.all()


def get_transactions_by_type(bank, transaction_type):
    return bank.transactions.filter(type=transaction_type)


def add_income(bank, amount):
    if amount <= 0:
        raise ValueError("The value must be positive!")
    bank.total_income += amount
    bank.balance += amount
    bank.save()


def add_expense(bank, amount):
    """Add expense to the bank."""
    if amount <= 0:
        raise ValueError("The value must be positive!")
    if bank.balance < amount:
        raise ValueError("Not Enough Money!")
    bank.total_expenses += amount
    bank.balance -= amount
    bank.save()


def create_transaction(bank, transaction_type, amount, description="", team=None):
    validate_transaction_type(transaction_type)
    season = get_current_season()

    if amount <= 0:
        raise ValueError("The value must be positive!")

    with transaction.atomic():
        if transaction_type == 'IN':
            add_income(bank, amount)
        elif transaction_type == 'OUT':
            add_expense(bank, amount)

        return Transaction.objects.create(
            bank=bank,
            type=transaction_type,
            amount=amount,
            description=description or "No description provided",
            team=team,
            season=season  # Ново поле
        )


def validate_transaction_type(transaction_type):
    """Validate the transaction type."""
    if transaction_type not in ['IN', 'OUT']:
        raise ValueError("Invalid transaction type")
