import os
import random
import shutil
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

# за createplayerutils
def generate_random_player(team=None, position=None):
    """
    Генерира произволен играч с произволни атрибути и го добавя в даден отбор (ако е зададен).
    """
    nationalities = Nationality.objects.all()
    positions = Position.objects.all()
    attributes = {attr.name: random.randint(1, 20) for attr in Attribute.objects.all()}
    nationality = random.choice(nationalities)
    region = nationality.region
    team_player_numbers = set(TeamPlayer.objects.filter(team=team).values_list('shirt_number', flat=True))

    first_name, last_name = get_player_random_first_and_last_name(region)
    if position is None:
        position = random.choice(positions)

    for pos_attr in position.positionattribute_set.all():
        base_value = attributes.get(pos_attr.attribute.name, 1)
        boosted_value = min(int(base_value * (1 + (pos_attr.importance - 1) * 0.3)), 20)
        attributes[pos_attr.attribute.name] = boosted_value

    age = random.randint(18, 35)

    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age=age,
        position=position,
    )
    player.save()

    PlayerAttribute.objects.bulk_create([
        PlayerAttribute(player=player, attribute=Attribute.objects.get(name=attr_name), value=value)
        for attr_name, value in attributes.items()
    ])

    player.price = update_player_price(player)
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    player.photo = copy_player_image_to_static(photo_folder="E:/Data/playersImages", player_id=player.id,
                                               static_path=static_path)

    while True:
        random_number = random.randint(1, 99)
        if random_number not in team_player_numbers:
            break
    player.save()

    if team:
        TeamPlayer.objects.create(player=player, team=team, shirt_number=random_number)

    return player

# за generateplayers_utils
def generate_team_players(team):
    """
    Генерира набор от играчи за даден отбор, включващи различни позиции.
    """
    positions = {
        'Goalkeeper': 1,
        'Defender': 4,
        'Midfielder': 4,
        'Attacker': 2,
        'Random': 5,
    }

    for pos_name, count in positions.items():
        position = Position.objects.get(name=pos_name.capitalize())
        for _ in range(count):
            generate_random_player(team, position if pos_name != 'Random' else None)