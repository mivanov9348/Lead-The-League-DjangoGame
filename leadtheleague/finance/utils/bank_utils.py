from decimal import Decimal

from django.db import transaction

from finance.models import Bank
from finance.utils.fund_utils import distribute_to_funds
from game.utils import get_setting_value


def get_bank():
    try:
        return Bank.objects.get(is_main=True)
    except Bank.DoesNotExist:
        raise ValueError("There is no Bank!")


def get_bank_balance(bank):
    return bank.balance


def get_bank_financials(bank):
    """Return a dictionary with the bank's financial summary."""
    return {
        "balance": bank.balance,
        "total_income": bank.total_income,
        "total_expenses": bank.total_expenses,
    }


def add_income(bank, amount):
    """Add income to the bank."""
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


def update_bank_balance(bank):
    """Update the bank's balance based on total income and expenses."""
    bank.balance = bank.total_income - bank.total_expenses
    bank.save()


def distribute_income(bank, amount):
    """Distribute income between the bank and funds."""
    if amount <= 0:
        raise ValueError("Amount must be positive!")

    # Преобразуваме процентите към Decimal
    bank_share_percentage = Decimal(str(get_setting_value("bank_share"))).quantize(Decimal("0.0001"))
    funds_share_percentage = Decimal(str(get_setting_value("fund_share"))).quantize(Decimal("0.0001"))

    # Проверяваме дали сумата от процентите е равна на 1 с малка допустима грешка
    total_percentage = bank_share_percentage + funds_share_percentage
    if total_percentage != Decimal("1"):
        raise ValueError(f"Bank and fund share percentages must sum to 1 (got {total_percentage}).")

    # Изчисляваме дяловете
    bank_share = amount * bank_share_percentage
    funds_share = amount * funds_share_percentage

    with transaction.atomic():
        add_income(bank, bank_share)
        distribute_to_funds(bank, funds_share)