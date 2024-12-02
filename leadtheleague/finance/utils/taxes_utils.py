from decimal import Decimal
from finance.utils.bank_utils import distribute_income
from game.utils import get_setting_value

# tax from transfer
def transfer_tax(bank, transfer_amount):
    """Apply a transfer tax and distribute it between the bank and funds."""
    transfer_tax_percentage = get_setting_value("transfer_tax")

    if transfer_tax_percentage <= 0:
        raise ValueError("Transfer tax percentage must be positive!")

    # Calculate the transfer tax
    transfer_tax = transfer_amount * Decimal(transfer_tax_percentage / 100)

    # Distribute the tax between the bank and funds
    distribute_income(bank, transfer_tax)

    return transfer_tax


# tax from agent for his selled player
def free_agent_transfer_tax(bank, transfer_amount):
    free_transfer_tax_percentage = get_setting_value('free_agent_tax')

    if free_transfer_tax_percentage <= 0:
        raise ValueError("Transfer tax percentage must be positive!")

    free_agent_tax = transfer_amount * Decimal(free_transfer_tax_percentage / 100)
    pass


def sponsorship_contract_tax(bank, contract_amount):
    """Calculate and apply the tax from a sponsorship contract."""
    sponsorship_tax_percentage = get_setting_value("sponsorship_tax")

    if sponsorship_tax_percentage <= 0:
        raise ValueError("Sponsorship tax percentage must be positive!")

    # Calculate the sponsorship tax
    sponsorship_tax = contract_amount * Decimal(sponsorship_tax_percentage / 100)

    # Distribute the tax between the bank and funds
    distribute_income(bank, sponsorship_tax)

    return sponsorship_tax


# Fine for yellow card
def yellow_card_fine(bank, player):
    """Apply a fine for a yellow card to a player."""
    yellow_card_fine_amount = get_setting_value("yellow_card_fine")

    if yellow_card_fine_amount <= 0:
        raise ValueError("Yellow card fine amount must be positive!")
    pass


# Fine for red card
def red_card_fine(bank, player):
    """Apply a fine for a red card to a player."""
    red_card_fine_amount = get_setting_value("red_card_fine")

    if red_card_fine_amount <= 0:
        raise ValueError("Red card fine amount must be positive!")
    pass