from django.db import transaction

from teams.utils.generate_team_utils import boost_reputation


def can_upgrade_stadium(stadium, tier):
    """
    Checks if the stadium can be upgraded to the given tier.
    """
    return stadium.tier is None or tier.level == stadium.tier.level + 1


@transaction.atomic
def upgrade_stadium(stadium, tier):
    """
    Upgrades the stadium to the given tier.
    Adjusts the stadium's attributes and related teams popularity.
    """
    if tier.level <= (stadium.tier.level if stadium.tier else 0):
        raise ValueError(f"Cannot downgrade or stay at the same level ({tier.level}).")

    stadium.tier = tier
    stadium.capacity = tier.capacity_boost
    stadium.ticket_price = tier.ticket_price
    stadium.save()

    team = stadium.team
    if team:
        boost_reputation(team, tier.popularity_bonus)
        team.save()
