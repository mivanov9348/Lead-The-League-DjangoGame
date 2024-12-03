import os
import random
import shutil
import logging
from game.models import Settings
from game.utils import get_setting_value
from leadtheleague import settings
from players.models import FirstName, LastName, Nationality, Position, Attribute, PlayerAttribute, Player, \
    PositionAttribute
from players.utils.update_player_stats_utils import update_player_price
from teams.models import TeamPlayer


def get_player_random_first_and_last_name(region):
    first_names = list(FirstName.objects.filter(region=region)) or list(FirstName.objects.all())
    last_names = list(LastName.objects.filter(region=region)) or list(LastName.objects.all())

    first_name = random.choice(first_names).name
    last_name = random.choice(last_names).name
    return first_name, last_name


def calculate_player_attributes(player):
    position = player.position
    age = player.age
    attributes = {}

    # Вземаме всички атрибути
    all_attributes = Attribute.objects.all()

    # Вземаме важността на атрибутите за позицията на играча
    position_importances = {
        pos_attr.attribute.id: pos_attr.importance
        for pos_attr in PositionAttribute.objects.filter(position=position)
    }

    for attribute in all_attributes:
        # Базова стойност
        base_value = 1

        # Важност на атрибута за позицията (ако няма зададена важност, приемаме 1)
        importance = position_importances.get(attribute.id, 1)

        # Увеличение на стойността според важността
        importance_factor = importance * 3  # Пример: важност 4 = +12, важност 1 = +3
        adjusted_value = base_value + importance_factor

        # Възрастов фактор (с минимална възраст 14 години)
        if age < 28:
            age_factor = max(0.8, min((age - 14) / 14 + 0.8, 1.2))  # Подобрение до 28 години
        else:
            age_factor = max(0.6, 1.2 - (age - 28) * 0.05)  # Намаление след 28 години

        age_adjusted_value = adjusted_value * age_factor

        # Добавяме случайност
        random_factor = random.uniform(0.9, 1.1)
        final_value = age_adjusted_value * random_factor

        # Ограничаваме стойността между 1 и 20
        final_value = min(max(round(final_value), 1), 20)

        # Запазваме резултата за този атрибут
        attributes[attribute] = final_value

    # Изчистваме старите атрибути на играча и създаваме нови
    PlayerAttribute.objects.filter(player=player).delete()
    PlayerAttribute.objects.bulk_create([
        PlayerAttribute(player=player, attribute=attr, value=value)
        for attr, value in attributes.items()
    ])

    return player  # Връщаме играча


def choose_random_photo(photo_folder):
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)


def copy_player_image_to_media(photo_folder, player_id):
    """
    Копира случайна снимка от photo_folder в media/playerimages и я преименува спрямо player_id.
    """
    # Път към папката media/playerimages
    player_images_folder = os.path.join(settings.MEDIA_ROOT, 'playerimages')

    # Избор на случайна снимка
    chosen_photo = choose_random_photo(photo_folder)
    if not os.path.exists(chosen_photo):
        print(f"The chosen photo {chosen_photo} doesn't exist.")
        return None

    # Проверка и създаване на папката, ако я няма
    if not os.path.exists(player_images_folder):
        os.makedirs(player_images_folder, exist_ok=True)

    # Ново име за снимката
    new_photo_path = os.path.join(player_images_folder, f"{player_id}.png")

    # Копиране на файла
    shutil.copy(chosen_photo, new_photo_path)

    # Връщане на относителния път за ImageField
    return f'playerimages/{player_id}.png'


def generate_random_player(team=None, position=None):
    """
    Генерира случаен играч, записва го в базата и създава негова снимка.
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

    photo_path = copy_player_image_to_media(
        photo_folder="E:/Data/playersImages",
        player_id=player.id
    )
    player.image = photo_path  # Задаваме снимката
    player.save()  # Запазваме промяната за снимката

    # Изчисляване и записване на атрибутите за играча
    player = calculate_player_attributes(player)

    # Актуализация на цената
    player.price = update_player_price(player)

    # Избиране на уникален номер
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

    # Генериране на нужните играчи на всяка позиция
    for pos_name, count in positions.items():
        try:
            position = Position.objects.get(name=pos_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"Позицията '{pos_name}' не съществува в базата данни.")
            continue

        for _ in range(int(count)):
            generate_random_player(team, position)

    # Генериране на допълнителни 5 случайни играча на случайни позиции
    all_positions = list(positions.keys())  # Списък с всички позиции
    for _ in range(random_players):
        random_position_name = random.choice(all_positions)
        try:
            random_position = Position.objects.get(name=random_position_name.capitalize())
        except Position.DoesNotExist:
            logging.error(f"Случайна позиция '{random_position_name}' не съществува в базата данни.")
            continue

        generate_random_player(team, random_position)

def generate_free_agents(agent):
    """
    Генерира свободни играчи за даден агент, като броят и позициите се определят на база на настройки.
    """

    # Вземане на стойности от настройките
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