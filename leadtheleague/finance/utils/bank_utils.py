from decimal import Decimal
from django.db import transaction
from finance.models import Bank
from finance.utils.fund_utils import distribute_to_funds
from finance.utils.transaction_utils import create_transaction
from game.utils.settings_utils import get_setting_value


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

def update_bank_balance(bank):
    bank.balance = bank.total_income - bank.total_expenses
    bank.save()

def distribute_income(bank, amount, description, team):
    if amount <= 0:
        raise ValueError("Amount must be positive!")
    amount = Decimal(amount)

    bank_share_percentage = Decimal(str(get_setting_value("bank_share"))).quantize(Decimal("0.0001"))
    funds_share_percentage = Decimal(str(get_setting_value("fund_share"))).quantize(Decimal("0.0001"))

    total_percentage = bank_share_percentage + funds_share_percentage
    if total_percentage != Decimal("1"):
        raise ValueError(f"Bank and fund share percentages must sum to 1 (got {total_percentage}).")

    bank_share = amount * bank_share_percentage
    funds_share = amount * funds_share_percentage

    with transaction.atomic():
        create_transaction(bank, 'IN', bank_share, description, team)
        distribute_to_funds(bank, funds_share)