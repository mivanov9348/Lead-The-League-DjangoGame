import datetime
from game.models import Season

def get_current_season():
    current_season = Season.objects.filter(is_active=True).first()
    if not current_season:
        raise ValueError("No active season found.")
    print(f"Current season: {current_season}")
    return current_season

def check_are_all_competition_completed(season):
    leagues_completed = not season.league_seasons.filter(is_completed=False).exists()
    cups_completed = not season.season_cups.filter(is_completed=False).exists()
    euro_cups_completed = not season.european_cup_seasons.filter(is_euro_cup_finished=False).exists()
    return leagues_completed and cups_completed and euro_cups_completed
