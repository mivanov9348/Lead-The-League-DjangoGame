import random
from core.models import Nationality


def get_all_nationalities():
    return Nationality.objects.all()


def get_random_nationality():
    all_nationalities = get_all_nationalities()
    random_nationality = random.choice(all_nationalities)
    return random_nationality


def get_nationality_region(nationality):
    return nationality.region