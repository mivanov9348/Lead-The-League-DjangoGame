from datetime import date

from game.models import Season

def get_current_season():
    return Season.objects.filter(is_active=True).first()

def check_are_all_competition_completed(season):
    leagues_completed = not season.league_seasons.filter(is_completed=False).exists()
    cups_completed = not season.season_cups.filter(is_completed=False).exists()
    euro_cups_completed = not season.european_cup_season_set.filter(knockout_stages__is_played=False).exists()
    return leagues_completed and cups_completed and euro_cups_completed

def finalize_season(season):
    if not check_are_all_competition_completed(season):
        return False

    season.is_ended = True
    season.is_active = False
    season.end_date = date.today()
    season.save()
    return True

def update_game():
    # relegated
    # promoted
    # eurocup participants
    # retired
    # result reset
    # player stats reset
    # fixtures new season
    # New Youth Intake
    pass