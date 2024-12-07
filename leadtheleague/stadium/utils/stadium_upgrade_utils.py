from stadium.models import StadiumTier


def upgrade_stadium(stadium, team):
    current_tier = stadium.tier
    next_tier = StadiumTier.objects.filter(level=current_tier.level + 1).first()

    if not next_tier:
        return {"success": False, "message": "There is no next level to upgrade!"}

    upgrade_cost = next_tier.capacity_boost * 100  # Примерна цена

    if team.budget < upgrade_cost:
        return {"success": False, "message": "No money!"}

    team.budget -= upgrade_cost
    stadium.tier = next_tier
    stadium.capacity += next_tier.capacity_boost
    stadium.ticket_price *= next_tier.ticket_price_multiplier
    stadium.maintenance_cost = next_tier.maintenance_cost
    stadium.save()
    team.save()

    return {"success": True, "message": f"The stadium is upgraded to {next_tier.name}!"}
