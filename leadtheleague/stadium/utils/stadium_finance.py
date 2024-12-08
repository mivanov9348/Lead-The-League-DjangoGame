def calculate_match_income(stadium, attendance_percentage):
    attendance = int(stadium.capacity * attendance_percentage)
    income = attendance * stadium.ticket_price
    return income


def calculate_monthly_maintenance(stadium):
    return stadium.maintenance_cost

