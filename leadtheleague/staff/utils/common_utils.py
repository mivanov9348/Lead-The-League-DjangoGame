import os
import random
import shutil

from leadtheleague import settings


def choose_random_photo(photo_folder):
    """
    Picks a random photo from the specified folder.
    """
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)


def copy_staff_image_to_media(photo_folder, staff_id):
    """
    Copies a random photo from the photo_folder to media/staffimages and renames it according to the agent_id.
    """
    # Path to the media/staffimages folder
    agent_images_folder = os.path.join(settings.MEDIA_ROOT, 'staffImages')

    # Choose a random photo
    chosen_photo = choose_random_photo(photo_folder)
    if not os.path.exists(chosen_photo):
        print(f"The chosen photo {chosen_photo} doesn't exist.")
        return None

    # Check and create the folder if it doesn't exist
    if not os.path.exists(agent_images_folder):
        os.makedirs(agent_images_folder, exist_ok=True)

    # New name for the photo
    new_photo_path = os.path.join(agent_images_folder, f"{staff_id}.png")

    # Copy the file
    shutil.copy(chosen_photo, new_photo_path)

    # Return the relative path for ImageField
    return f'staffImages/{staff_id}.png'