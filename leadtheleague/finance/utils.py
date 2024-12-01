from finance.models import Bank, Transaction
from django.db import models, transaction

def get_bank():
    try:
        return Bank.objects.get(is_main=True)
    except Bank.DoesNotExist:
        raise ValueError("There is no Bank!")


def get_bank_balance(bank):
    return bank.balance


def get_bank_financials(bank):
    return {
        "balance": bank.balance,
        "total_income": bank.total_income,
        "total_expenses": bank.total_expenses,
    }


def add_income(bank, amount):
    if amount <= 0:
        raise ValueError("The value must be positive!")
    bank.total_income += amount
    bank.balance += amount
    bank.save()


def add_expense(bank, amount):
    if amount <= 0:
        raise ValueError("The value must be positive!")
    if bank.balance >= amount:
        bank.total_expenses += amount
        bank.balance -= amount
        bank.save()
    else:
        raise ValueError("Not Enough Money!")


def update_bank_balance(bank):
    bank.balance = bank.total_income - bank.total_expenses
    bank.save()


# Transactions
def get_transactions_for_bank(bank):
    return bank.transactions.all()


def get_transactions_by_type(bank,transaction_type):
    return bank.transactions.filter(type=transaction_type)


def calculate_total_transactions(transaction_type):
    return Transaction.objects.filter(type=transaction_type).aggregate(total=models.Sum('amount'))['total'] or 0


def create_transaction(bank, transaction_type, amount, description=""):
    validate_transaction_type(transaction_type)

    with transaction.atomic():
        if transaction_type == 'IN':
            bank.total_income += amount
            bank.balance += amount
        elif transaction_type == 'OUT':
            if bank.balance < amount:
                raise ValueError("Not Enough Money!")
            bank.total_expenses += amount
            bank.balance -= amount

        bank.save()

        return Transaction.objects.create(
            bank=bank,
            type=transaction_type,
            amount=amount,
            description=description,
        )

def validate_transaction_type(transaction_type):
    if transaction_type not in ['IN', 'OUT']:
        raise ValueError("Invalid transaction type")
