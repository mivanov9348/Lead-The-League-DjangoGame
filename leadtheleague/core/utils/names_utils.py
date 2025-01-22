import random
from core.models import FirstName, LastName

# def get_random_first_name(region):
#     first_names = list(FirstName.objects.filter(region=region)) or list(FirstName.objects.all())
#     first_name = random.choice(first_names).name
#     return first_name
#
# def get_random_last_name(region):
#     last_names = list(LastName.objects.filter(region=region)) or list(LastName.objects.all())
#     last_name = random.choice(last_names).name
#     return last_name

def get_random_first_name(region, nationality=None):
    if nationality:
        names = list(FirstName.objects.filter(nationality=nationality))
    else:
        names = list(FirstName.objects.filter(region=region, nationality__isnull=True))

    if not names:
        names = list(FirstName.objects.all())

    return random.choice(names).name

def get_random_last_name(region, nationality=None):
    if nationality:
        last_names = list(LastName.objects.filter(nationality=nationality))
    else:
        last_names = list(LastName.objects.filter(region=region, nationality__isnull=True))

    if not last_names:  # Ако няма резултати, вземи всички
        last_names = list(LastName.objects.all())

    return random.choice(last_names).name
