import math
import os
import random
import shutil
import logging
from django.db import transaction
from core.utils.names_utils import get_random_first_name, get_random_last_name
from core.utils.nationality_utils import get_all_nationalities, get_random_nationality_priority
from game.models import Settings
from game.utils.settings_utils import get_setting_value
from leadtheleague import settings
from players.models import Position, Attribute, PlayerAttribute, Player, PositionAttribute, Statistic, \
    PlayerSeasonStatistic
from players.utils.update_player_stats_utils import update_player_price
from teams.models import TeamPlayer


def calculate_player_attributes(player):
    position = player.position
    age = player.age
    attributes = {}

    # Getting All Attributes
    all_attributes = Attribute.objects.all()

    # Getting Attributes Weights
    position_importances = {
        pos_attr.attribute.id: pos_attr.importance
        for pos_attr in PositionAttribute.objects.filter(position=position)
    }

    for attribute in all_attributes:
        # Based Value
        base_value = 1

        # Важност на атрибута за позицията (ако няма зададена важност, приемаме 1)
        importance = position_importances.get(attribute.id, 1)

        # Увеличение на стойността според важността
        importance_factor = importance * 3  # Пример: важност 4 = +12, важност 1 = +3
        adjusted_value = base_value + importance_factor

        # Възрастов фактор (с минимална възраст 14 години)
        if age < 28:
            age_factor = max(0.8, min((age - 14) / 14 + 0.8, 1.2))
        else:
            age_factor = max(0.6, 1.2 - (age - 28) * 0.05)

        age_adjusted_value = adjusted_value * age_factor

        # Добавяме случайност
        random_factor = random.uniform(0.9, 1.1)
        final_value = age_adjusted_value * random_factor

        # Ограничаваме стойността между 1 и 20
        final_value = min(max(round(final_value), 1), 20)

        progress_value = random.uniform(0.0, 1.0)

        # Запазваме резултата за този атрибут
        attributes[attribute] = (final_value, progress_value)

    PlayerAttribute.objects.filter(player=player).delete()
    PlayerAttribute.objects.bulk_create([
        PlayerAttribute(player=player, attribute=attr, value=value, progress=progress)
        for attr, (value, progress) in attributes.items()
    ])

    return player


def get_potential_age_factor(player):
    # Get age factor for potential

    if player.age <= 17:
        age_factor = 1.3
    elif 18 <= player.age <= 25:
        age_factor = 1.0
    elif 26 <= player.age <= 30:
        age_factor = 0.7
    else:
        age_factor = 0.5
    return age_factor


def calculate_player_potential(player):
    base_potential = 0.1

    attributes = PlayerAttribute.objects.filter(player=player)
    attribute_dict = {attr.attribute.name: attr.value for attr in attributes}

    technical_attributes = ['Dribbling', 'Passing', 'Shooting']
    physical_attributes = ['Speed', 'Strength']

    determination = PlayerAttribute.objects.get(player=player, attribute__name='Determination').value
    workrate = PlayerAttribute.objects.get(player=player, attribute__name='WorkRate').value

    technical_average = sum(attribute_dict.get(attr, 1) for attr in technical_attributes) / len(technical_attributes)
    physical_average = sum(attribute_dict.get(attr, 1) for attr in physical_attributes) / len(physical_attributes)

    growth_factors = (
            (determination / 20) * 1.2 +
            (workrate / 20) * 1.0 +
            (technical_average / 20) * 1.1 +
            (physical_average / 20) * 0.8
    )

    random_factor = random.uniform(-0.1, 0.1)

    # Изчисление на потенциала
    potential = base_potential + growth_factors + random_factor
    potential *= get_potential_age_factor(player)

    # Ограничаване и нормализация
    potential = math.pow(potential, 0.9)
    return min(max(potential, 0.1), 5.0)


def choose_random_photo(photo_folder):
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)

def copy_player_image_to_media(photo_folder, player_id):
    """
    Copies a random photo from the photo_folder to media/playerimages and renames it according to the player_id.
    """
    # Path to the media/playerimages folder
    player_images_folder = os.path.join(settings.MEDIA_ROOT, 'playerimages')

    # Choose a random photo
    chosen_photo = choose_random_photo(photo_folder)
    if not os.path.exists(chosen_photo):
        print(f"The chosen photo {chosen_photo} doesn't exist.")
        return None

    # Check and create the folder if it doesn't exist
    if not os.path.exists(player_images_folder):
        os.makedirs(player_images_folder, exist_ok=True)

    # New name for the photo
    new_photo_path = os.path.join(player_images_folder, f"{player_id}.png")

    # Copy the file
    shutil.copy(chosen_photo, new_photo_path)

    # Return the relative path for ImageField
    return f'playerimages/{player_id}.png'


def generate_random_player(team=None, position=None, age=None):
    nationalities = get_all_nationalities()
    positions = Position.objects.all()

    if team:
        team_nationality = team.nationality
        nationality = get_random_nationality_priority(team_nationality, 0.8)  # за settings
    else:
        nationality = random.choice(nationalities)

    region = nationality.region
    team_player_numbers = set(TeamPlayer.objects.filter(team=team).values_list('shirt_number', flat=True))
    first_name = get_random_first_name(region)
    last_name = get_random_last_name(region)

    if position is None:
        position = random.choice(positions)

    age = random.randint(18, 35)
    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age=age,
        position=position,
    )
    player.save()

    photo_path = copy_player_image_to_media(
        photo_folder="E:/Data/playersImages",
        player_id=player.id
    )
    player.image = photo_path
    player.save()

    player = calculate_player_attributes(player)

    player.price = update_player_price(player)

    player.potential_rating = calculate_player_potential(player)

    while True:
        random_number = random.randint(1, 99)
        if random_number not in team_player_numbers:
            break

    player.save()
    if team:
        TeamPlayer.objects.create(player=player, team=team, shirt_number=random_number)

    return player


def generate_team_players(team):
    try:
        min_goalkeepers = Settings.objects.get(name='Minimum_Goalkeepers_By_Team').value
    except Settings.DoesNotExist:
        logging.error("Настройката 'Minimum_Goalkeepers_By_Team' не съществува.")
        min_goalkeepers = 1  # Стойност по подразбиране

    try:
        min_defenders = Settings.objects.get(name='Minimum_Defenders_By_Team').value
    except Settings.DoesNotExist:
        logging.error("Настройката 'Minimum_Defenders_By_Team' не съществува.")
        min_defenders = 4  # Стойност по подразбиране

    try:
        min_midfielders = Settings.objects.get(name='Minimum_Midfielders_By_Team').value
    except Settings.DoesNotExist:
        logging.error("Настройката 'Minimum_Midfielders_By_Team' не съществува.")
        min_midfielders = 4  # Стойност по подразбиране

    try:
        min_attackers = Settings.objects.get(name='Minimum_Attackers_By_Team').value
    except Settings.DoesNotExist:
        logging.error("Настройката 'Minimum_Attackers_By_Team' не съществува.")
        min_attackers = 2  # Стойност по подразбиране

    try:
        random_players = int(Settings.objects.get(name='Random_Players_Generate').value)
    except Settings.DoesNotExist:
        logging.error("Настройката 'Random_Players_Generate' не съществува.")
        random_players = 5

    positions = {
        'Goalkeeper': min_goalkeepers,
        'Defender': min_defenders,
        'Midfielder': min_midfielders,
        'Attacker': min_attackers,
    }

    for pos_name, count in positions.items():
        try:
            position = Position.objects.get(name=pos_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"Позицията '{pos_name}' не съществува в базата данни.")
            continue

        for _ in range(int(count)):
            generate_random_player(team, position)

    all_positions = list(positions.keys())
    for _ in range(random_players):
        random_position_name = random.choice(all_positions)
        try:
            random_position = Position.objects.get(name=random_position_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"Случайна позиция '{random_position_name}' не съществува в базата данни.")
            continue

        generate_random_player(team, random_position)


def generate_free_agents(agent):
    try:
        min_free_agents = int(get_setting_value('minimum_free_agents'))
        max_free_agents = int(get_setting_value('maximum_free_agents'))
    except ValueError as e:
        logging.error(f"Error fetching settings: {e}")
        return []

    # Генериране на случайна бройка играчи за агента в зададения диапазон
    total_free_agents = random.randint(min_free_agents, max_free_agents)

    # Разпределяне на играчите между позициите
    position_distribution = {
        'Goalkeeper': 0,
        'Defender': 0,
        'Midfielder': 0,
        'Attacker': 0,
    }

    remaining_players = total_free_agents
    positions = list(position_distribution.keys())

    for pos in positions[:-1]:
        count = random.randint(0, remaining_players)
        position_distribution[pos] = count
        remaining_players -= count

    # Останалите играчи отиват в последната позиция
    position_distribution[positions[-1]] = remaining_players

    free_agents = []
    for pos_name, count in position_distribution.items():
        try:
            position = Position.objects.get(name=pos_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"The position '{pos_name}' doesn't exist!")
            continue

        for _ in range(count):
            # Генериране на произволен играч
            player = generate_random_player(team=None, position=position)
            player.is_free_agent = True
            player.agent = agent
            player.save()
            free_agents.append(player)

    return free_agents


def retirement_player(player):
    if player.age >= 35:
        player.is_active = False
        player.save()
        TeamPlayer.objects.filter(player=player).delete()


def generate_youth_player(team=None):
    """
    Generate youth player.
    """
    player = generate_random_player(team=team)
    player.age = random.randint(14, 17)  # за settings
    player.is_youth = True

    player.potential_rating = calculate_player_potential(player)

    player.save()
    return player


def generate_player_season_stats(player, new_season, team):
    statistics = Statistic.objects.all()
    with transaction.atomic():
        for stat in statistics:
            # Проверка дали статистиката вече съществува за играча в този сезон
            if not PlayerSeasonStatistic.objects.filter(player=player, statistic=stat, season=new_season).exists():
                # Създаване на запис със стойност по подразбиране 0
                PlayerSeasonStatistic.objects.create(
                    player=player,
                    statistic=stat,
                    season=new_season,
                    value=0
                )
