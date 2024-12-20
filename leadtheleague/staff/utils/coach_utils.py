import random
from core.utils.names_utils import get_random_first_name, get_random_last_name
from core.utils.nationality_utils import get_random_nationality, get_nationality_region
from game.utils.settings_utils import get_setting_value
from staff.models import Coach

def get_coaches_without_team():
    coaches = Coach.objects.filter(team__isnull=True)
    return coaches

def calculate_coach_price(rating):
    base_price = int(get_setting_value('coach_base_price'))
    price_coefficient = get_setting_value('coach_price_coefficient')
    return base_price * (1 + rating * price_coefficient)

def generate_coach():
    random_nationality = get_random_nationality()
    region = get_nationality_region(random_nationality)

    first_name = get_random_first_name(region)
    last_name = get_random_last_name(region)

    age = random.randint(30, 60)
    rating = round(random.uniform(1.0, 10.0), 1)
    price = calculate_coach_price(rating)

    coach = Coach.objects.create(
        first_name=first_name,
        last_name=last_name,
        age=age,
        rating=rating,
        price=price
    )
    return coach

def buy_coach(team, coach_id):
    coach = Coach.objects.filter(id=coach_id, team__isnull=True).first()
    if not coach:
        return "Coach is not available."

    if team.balance < coach.price:
        return "Not enough balance."

    team.coach = coach
    team.balance -= coach.price
    team.save()

    return f"Coach {coach} has been hired by team {team.name}!"