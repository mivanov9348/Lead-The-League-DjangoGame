import random
from datetime import timezone, datetime, timedelta
from .models import Player, FirstName, LastName, Team, Nationality, Position, PositionAttribute, PlayerAttribute, Attribute

def calculate_player_price(player):

    base_prices={
        'Goalkeeper': 20000,
        'Defender': 30000,
        'Midfielder': 40000,
        'Attacker': 50000
    }

    base_price = base_prices.get(player.position.position_name,2500)

    if player.age <25:
        age_factor = 1.2
    elif player.age > 30:
        age_factor = 0.8
    else:
        age_factor = 1.0

    total_attributes = sum(PlayerAttribute.objects.filter(player=player).values_list('value', flat=True))
    price = int(base_price * age_factor + total_attributes * 100)
    return price

def generate_random_player(team = None, position = None):
    nationalities = Nationality.objects.all()
    nationality = random.choice(nationalities)

    region = nationality.region

    first_names = list(FirstName.objects.filter(region=region))
    last_names = list(LastName.objects.filter(region=region))

    if not first_names:  # If there are no first names for the nationality
        first_names = list(FirstName.objects.all())

    if not last_names:  # If there are no last names for the nationality
        last_names = list(LastName.objects.all())

    first_name = random.choice(first_names).name
    last_name = random.choice(last_names).name

    if position is None:
        position = random.choice(Position.objects.all())

    # Initialize all attributes
    attributes = {attr.name: random.randint(1, 20) for attr in Attribute.objects.all()}

    # Get position attributes for the player's position
    position_attributes = PositionAttribute.objects.filter(position=position)

    # Adjust values based on the importance for the position
    for pos_attr in position_attributes:
        if pos_attr.attribute.name in attributes:  # Ensure the attribute exists in the player attributes
            # Multiply the base value by a factor related to the importance
            value = attributes[pos_attr.attribute.name] * (pos_attr.importance / 4)
            attributes[pos_attr.attribute.name] = int(value)  # Assign adjusted value

    age = random.randint(18,35)

    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age = age,
        position=position,
        team = team
    )
    player.save()

    # Create PlayerAttribute instances for all attributes
    for attr_name, value in attributes.items():
        attr = Attribute.objects.get(name=attr_name)  # Get the Attribute instance
        PlayerAttribute.objects.create(player=player, attribute=attr, value=value)

    player.price = calculate_player_price(player)
    player.save()

    return player

def generate_team_players(team):

    position_gk = Position.objects.get(position_name='Goalkeeper')
    position_def = Position.objects.get(position_name='Defender')
    position_mid = Position.objects.get(position_name='Midfielder')
    position_st = Position.objects.get(position_name='Attacker')

    generate_random_player(team, position_gk)

    for _ in range(4):
        generate_random_player(team, position_def)

    for _ in range(4):
        generate_random_player(team, position_mid)

    for _ in range(2):
        generate_random_player(team, position_st)

    all_positions = Position.objects.all()

    for _ in range(5):
        random_position = random.choice(all_positions)
        generate_random_player(team, random_position)

