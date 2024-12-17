from game.models import Season

def get_current_season():
    return Season.objects.filter(is_active=True).first()