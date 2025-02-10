import random
from decimal import Decimal
from core.utils.names_utils import get_random_first_name, get_random_last_name
from core.utils.nationality_utils import get_random_nationality, get_nationality_region
from game.utils.settings_utils import get_setting_value
from staff.models import Coach
from staff.utils.common_utils import copy_staff_image_to_media


def get_coaches_without_team():
    coaches = Coach.objects.filter(team__isnull=True)
    print(coaches)
    return coaches


def calculate_coach_price(rating):
    base_price = Decimal(get_setting_value('coach_base_price'))
    price_coefficient = Decimal(str(get_setting_value('coach_price_coefficient')))
    return base_price * (1 + rating * price_coefficient)


def new_seasons_coaches():
    coaches_count = int(get_setting_value('coaches_count_per_season'))
    coaches = [generate_coach() for _ in range(coaches_count)]

def generate_coach():
    random_nationality = get_random_nationality()
    region = get_nationality_region(random_nationality)

    first_name = get_random_first_name(region)
    last_name = get_random_last_name(region)

    age = random.randint(int(get_setting_value('coach_minimum_age')), int(get_setting_value('coach_maximum_age')))
    rating = Decimal(str(random.uniform(1.0, 10.0))).quantize(Decimal('0.1'))

    price = calculate_coach_price(rating)

    coach = Coach.objects.create(
        first_name=first_name,
        last_name=last_name,
        age=age,
        rating=rating,
        price=price
    )

    # Copy a random photo and link it to the coach
    photo_path = copy_staff_image_to_media(
        photo_folder="E:/Data/staffImages",
        staff_id=coach.id
    )
    if photo_path:
        coach.image = photo_path
        coach.save()
    else:
        print(f"Coach {coach.id} ({coach.first_name} {coach.last_name}) saved without an image.")

    return coach
