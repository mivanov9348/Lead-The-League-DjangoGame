import os
import random
import shutil
from setuptools import logging
from game.models import Settings
from players.models import FirstName, LastName, Nationality, Position, Attribute, PlayerAttribute, Player
from players.utils.update_player_stats_utils import update_player_price
from teams.models import TeamPlayer

def get_player_random_first_and_last_name(region):
    """
    Избира произволно име и фамилия на базата на региона.
    """
    first_names = list(FirstName.objects.filter(region=region)) or list(FirstName.objects.all())
    last_names = list(LastName.objects.filter(region=region)) or list(LastName.objects.all())

    first_name = random.choice(first_names).name
    last_name = random.choice(last_names).name
    return first_name, last_name


# за createplayerutils
def choose_random_photo(photo_folder):
    """
    Избира произволно снимка от дадената папка.
    """
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)


# за createplayerutils
def copy_player_image_to_static(photo_folder, player_id, static_path):
    """
    Копира избраната снимка на играча в статичната директория.
    """
    chosen_photo = choose_random_photo(photo_folder)
    if not os.path.exists(chosen_photo):
        print(f"The {chosen_photo} doesn't exist.")
        return None

    new_photo_path = os.path.join(static_path, 'playerimages', f"{player_id}.png")
    os.makedirs(os.path.dirname(new_photo_path), exist_ok=True)
    shutil.copy(chosen_photo, new_photo_path)

    return f'playerimages/{player_id}.png'

def calculate_player_attributes(player):
    """
    Изчислява атрибутите на играча въз основа на важността им за позицията, възрастта и случайност, след което ги запазва.
    """
    position = player.position
    age = player.age
    attributes = {}

    for pos_attr in position.positionattribute_set.all():
        # Базова стойност за всеки атрибут
        base_value = 5

        # Увеличаване според важността
        importance_factor = pos_attr.importance * 3  # Важност 4 ще даде +12, важност 1 ще даде +3
        adjusted_value = base_value + importance_factor

        # Възрастов фактор: По-младите играчи имат по-ниски стойности
        age_factor = max(0.8, min((age - 18) / 10, 1.2))  # Възраст между 18 и 30 има позитивен ефект
        age_adjusted_value = adjusted_value * age_factor

        # Добавяме случайност
        random_factor = random.uniform(0.9, 1.1)  # Малка вариация
        final_value = age_adjusted_value * random_factor

        # Гарантираме, че стойността е в рамките на 1 до 20
        final_value = min(max(round(final_value), 1), 20)

        attributes[pos_attr.attribute] = final_value

    # Запазване на атрибутите в базата данни
    PlayerAttribute.objects.bulk_create([
        PlayerAttribute(player=player, attribute=attr, value=value)
        for attr, value in attributes.items()
    ])

    return player  # Връщаме играча

def generate_random_player(team=None, position=None):
    """
    Генерира произволен играч и го добавя в даден отбор (ако е зададен).
    """
    nationalities = Nationality.objects.all()
    positions = Position.objects.all()
    nationality = random.choice(nationalities)
    region = nationality.region
    team_player_numbers = set(TeamPlayer.objects.filter(team=team).values_list('shirt_number', flat=True))
    first_name, last_name = get_player_random_first_and_last_name(region)
    if position is None:
        position = random.choice(positions)

    # Създаване на играча
    age = random.randint(18, 35)
    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age=age,
        position=position,
    )
    player.save()

    # Изчисляване и записване на атрибутите за играча
    player = calculate_player_attributes(player)

    # Актуализация на цената
    player.price = update_player_price(player)
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    player.photo = copy_player_image_to_static(photo_folder="E:/Data/playersImages", player_id=player.id,
                                               static_path=static_path)

    # Генериране на уникален номер
    while True:
        random_number = random.randint(1, 99)
        if random_number not in team_player_numbers:
            break
    player.save()

    if team:
        TeamPlayer.objects.create(player=player, team=team, shirt_number=random_number)

    return player


def generate_team_players(team):
    """
    Генерира набор от играчи за даден отбор, включващи различни позиции.
    """
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
        random_players = Settings.objects.get(name='Random_Players_Generate').value
    except Settings.DoesNotExist:
        logging.error("Настройката 'Random_Players_Generate' не съществува.")
        random_players = 0  # Стойност по подразбиране

    positions = {
        'Goalkeeper': min_goalkeepers,
        'Defender': min_defenders,
        'Midfielder': min_midfielders,
        'Attacker': min_attackers,
        'Random': random_players,
    }

    for pos_name, count in positions.items():
        try:
            position = Position.objects.get(name=pos_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"Позицията '{pos_name}' не съществува в базата данни.")
            continue

        for _ in range(int(count)):
            generate_random_player(team, position if pos_name != 'Random' else None)
