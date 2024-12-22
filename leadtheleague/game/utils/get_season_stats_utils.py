import datetime
from game.models import Season

def get_current_season():
    return Season.objects.filter(is_active=True).first()

def check_are_all_competition_completed(season):
    leagues_completed = not season.league_seasons.filter(is_completed=False).exists()
    cups_completed = not season.season_cups.filter(is_completed=False).exists()
    euro_cups_completed = not season.european_cup_seasons.filter(knockout_stages__is_played=False).exists()
    return leagues_completed and cups_completed and euro_cups_completed

