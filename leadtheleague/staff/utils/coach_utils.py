import random
from game.utils import get_setting_value
from players.models import Nationality, FirstName, LastName
from staff.models import Coach

def get_coaches_without_team():
    coaches = Coach.objects.filter(team__isnull=True)
    return coaches

def calculate_coach_price(rating):
    base_price = int(get_setting_value('coach_base_price'))
    price_coefficient = get_setting_value('coach_price_coefficient')
    return base_price * (1 + rating * price_coefficient)

def generate_coach():
    nationalities = Nationality.objects.all()
    nationality = random.choice(nationalities)
    region = nationality.region

    first_names = list(FirstName.objects.filter(region=region)) or list(FirstName.objects.all())
    last_names = list(LastName.objects.filter(region=region)) or list(LastName.objects.all())

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
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