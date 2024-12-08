from game.models import Season


def get_current_season(year=None):
    if year is not None:
        current_season = Season.objects.filter(year=year).order_by('-season_number').first()
    else:
        current_season = Season.objects.filter(is_ended=False).order_by('-season_number').first()
    return current_season