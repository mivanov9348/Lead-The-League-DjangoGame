from stadium.models import Stadium, StadiumTier


def get_team_stadium(team):
    try:
        return Stadium.objects.get(team_id=team.id)
    except Stadium.DoesNotExist:
        return None

def get_stadium_info(stadium):
    if not stadium:
        return {"error": "Stadium is not found."}

    return {
        "name": stadium.name,
        "teams": stadium.team.name,
        "tier": stadium.tier.name if stadium.tier else "Default Tier",
        "capacity": stadium.capacity,
        "ticket_price": stadium.ticket_price,
        "maintenance_cost": stadium.maintenance_cost,
    }


def get_next_stadium_tier(current_tier):
    if current_tier:
        return StadiumTier.objects.filter(level=current_tier.level + 1).first()
    return StadiumTier.objects.filter(level=1).first()
