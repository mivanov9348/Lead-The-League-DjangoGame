import random
from core.models import Nationality


def get_all_nationalities():
    return Nationality.objects.all()


def get_random_nationality():
    all_nationalities = get_all_nationalities()
    random_nationality = random.choice(all_nationalities)
    return random_nationality


def get_random_nationality_priority(priority_nationality, priority_chance=0.8):
    all_nationalities = get_all_nationalities()
    if random.random() < priority_chance:
        return priority_nationality
    else:
        other_nationalities = [n for n in all_nationalities if n != priority_nationality]
        return random.choice(other_nationalities)

def get_nationality_region(nationality):
    return nationality.region