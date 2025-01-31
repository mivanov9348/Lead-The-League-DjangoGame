import datetime
from django.db.models import Q
from game.models import Season


# def advance_day(self):
#     if self.current_date < self.end_date:
#         self.current_date += timezone.timedelta(days=1)
#         self.save()
#         # Извикване на логика за обработка на текущия ден
#         TeamState.process_all_teams(self)

def get_current_season():
    current_season = Season.objects.filter(is_active=True).first()
    if not current_season:
        raise ValueError("No active season found.")
    print(f"Current season: {current_season}")
    return current_season

def get_previous_season(current_season):
    return (
        Season.objects.filter(
            Q(year__lt=current_season.year) |
            Q(year=current_season.year, season_number__lt=current_season.season_number),
            is_ended=True
        )
        .order_by('-year', '-season_number')
        .first()
    )

def check_are_all_competition_completed(season):
    leagues_completed = not season.league_seasons.filter(is_completed=False).exists()
    cups_completed = not season.season_cups.filter(is_completed=False).exists()
    euro_cups_completed = not season.european_cup_seasons.filter(is_euro_cup_finished=False).exists()
    return leagues_completed and cups_completed and euro_cups_completed
