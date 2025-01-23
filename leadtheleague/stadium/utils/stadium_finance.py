from match.utils.match.attendance import calculate_match_income


def get_match_income(match):
    income = calculate_match_income(match, match.home_team)
    return income


def calculate_monthly_maintenance(stadium):
    return stadium.maintenance_cost

