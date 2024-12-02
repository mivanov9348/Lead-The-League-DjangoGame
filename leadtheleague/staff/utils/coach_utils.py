import random

from players.models import Nationality, FirstName, LastName
from staff.models import Coach

def generate_coaches():
    nationalities = Nationality.objects.all()
    nationality = random.choice(nationalities)
    region = nationality.region

    first_names = list(FirstName.objects.filter(region=region)) or list(FirstName.objects.all())
    last_names = list(LastName.objects.filter(region=region)) or list(LastName.objects.all())

    coaches = []
    for _ in range(200):  # Генерираме 200 треньори
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        age = random.randint(30, 60)
        rating = round(random.uniform(1.0, 10.0), 1)

        coach = Coach.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            rating=rating
        )
        coaches.append(coach)
    return coaches

def buy_coach(team, coach_id):

    # Проверяваме дали треньорът е свободен
    coach = Coach.objects.filter(id=coach_id, team__isnull=True).first()
    if not coach:
        return "Coach is not available."

    # Проверка за баланс на отбора
    if team.balance < coach.price:
        return "Not enough balance."

    # Купуване
    team.coach = coach
    team.balance -= coach.price
    team.save()

    return f"Coach {coach} has been hired by team {team.name}!"