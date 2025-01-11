import os
import random
import shutil
from decimal import Decimal

from django.core.files.base import ContentFile
from setuptools import logging

from core.utils.names_utils import get_random_first_name, get_random_last_name
from core.utils.nationality_utils import get_random_nationality, get_nationality_region
from game.utils.settings_utils import get_setting_value
from leadtheleague import settings
from messaging.utils.category_messages_utils import create_new_coach_message
from staff.models import Coach
from teams.utils.team_finance_utils import team_expense


def get_coaches_without_team():
    coaches = Coach.objects.filter(team__isnull=True)
    print(coaches)
    return coaches

def calculate_coach_price(rating):
    base_price = Decimal(get_setting_value('coach_base_price'))
    price_coefficient = Decimal(str(get_setting_value('coach_price_coefficient')))
    return base_price * (1 + rating * price_coefficient)


def new_seasons_coaches():
    coaches_count = int(get_setting_value('coaches_count'))
    coaches = [generate_coach() for _ in range(coaches_count)]

def choose_random_photo(photo_folder):
    """
    Picks a random photo from the specified folder.
    """
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)

def copy_coach_image_to_media(photo_folder, coach_id):
    """
    Copies a random photo from the photo_folder to media/staffimages and renames it according to the coach_id.
    """
    # Path to the media/staffimages folder
    coach_images_folder = os.path.join(settings.MEDIA_ROOT, 'staffImages')

    # Choose a random photo
    chosen_photo = choose_random_photo(photo_folder)
    if not os.path.exists(chosen_photo):
        print(f"The chosen photo {chosen_photo} doesn't exist.")
        return None

    # Check and create the folder if it doesn't exist
    if not os.path.exists(coach_images_folder):
        os.makedirs(coach_images_folder, exist_ok=True)

    # New name for the photo
    new_photo_path = os.path.join(coach_images_folder, f"{coach_id}.png")

    # Copy the file
    shutil.copy(chosen_photo, new_photo_path)

    # Return the relative path for ImageField
    return f'staffImages/{coach_id}.png'

def generate_coach():
    random_nationality = get_random_nationality()
    region = get_nationality_region(random_nationality)

    first_name = get_random_first_name(region)
    last_name = get_random_last_name(region)

    age = random.randint(30, 60)
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
    photo_path = copy_coach_image_to_media(
        photo_folder="E:/Data/staffImages",
        coach_id=coach.id
    )
    if photo_path:
        coach.image = photo_path
        coach.save()
    else:
        print(f"Coach {coach.id} ({coach.first_name} {coach.last_name}) saved without an image.")

    return coach

