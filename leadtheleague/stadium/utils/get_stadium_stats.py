from stadium.models import Stadium

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
