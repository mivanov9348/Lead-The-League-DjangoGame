from decimal import Decimal

from django.db import transaction
from finance.models import Fund
from game.utils import get_setting_value


def add_fund_income(fund, amount):
    """Add income to a fund."""
    if amount <= 0:
        raise ValueError("Amount must be positive!")

    with transaction.atomic():
        fund.total_income += amount
        fund.balance += amount
        fund.save()


def add_fund_expense(fund, amount):
    """Add an expense to a fund."""
    if amount <= 0:
        raise ValueError("Amount must be positive!")

    with transaction.atomic():
        if fund.balance < amount:
            raise ValueError("Not Enough Money in Fund!")
        fund.total_expense += amount
        fund.balance -= amount
        fund.save()


def distribute_to_funds(bank, funds_share):
    """Distribute a specific amount to all funds."""
    fund_keys = {
        "Match Fund": "match_fund",
        "League Fund": "league_fund",
        "Cup Fund": "cup_fund",
        "Global Fund": "global_fund",
    }

    if funds_share <= 0:
        raise ValueError("Funds share must be positive!")

    with transaction.atomic():
        for fund_name, key in fund_keys.items():
            # Преобразуване на процента към Decimal
            percentage = Decimal(str(get_setting_value(key)))

            # Изчисляване на дела за фонда
            amount = funds_share * percentage

            if amount > 0:
                try:
                    fund = Fund.objects.get(bank=bank, name=fund_name)
                    add_fund_income(fund, amount)
                except Fund.DoesNotExist:
                    raise ValueError(f"Fund '{fund_name}' does not exist for the given bank!")
