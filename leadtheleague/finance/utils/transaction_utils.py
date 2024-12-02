from django.db import transaction
from django.db.models import Sum

from finance.models import Transaction
from finance.utils.bank_utils import add_income, add_expense


def get_transactions_for_bank(bank):
    """Get all transactions related to the bank."""
    return bank.transactions.all()


def get_transactions_by_type(bank, transaction_type):
    """Get transactions of a specific type (IN/OUT) for the bank."""
    return bank.transactions.filter(type=transaction_type)


def calculate_total_transactions(transaction_type):
    """Calculate the total amount for all transactions of a specific type."""
    return Transaction.objects.filter(type=transaction_type).aggregate(total=Sum('amount'))['total'] or 0


def create_transaction(bank, transaction_type, amount, description=""):
    """Create a transaction and update the bank's financials."""
    validate_transaction_type(transaction_type)

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
        )


def validate_transaction_type(transaction_type):
    """Validate the transaction type."""
    if transaction_type not in ['IN', 'OUT']:
        raise ValueError("Invalid transaction type")
