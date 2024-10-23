import random
from datetime import timezone, datetime, timedelta
from .models import Player, FirstName, LastName, Team, Nationality, Position, PositionAttribute, PlayerAttribute, Attribute

def generate_random_player():
    nationalities = Nationality.objects.all()
    nationality = random.choice(nationalities)

    first_names = list(FirstName.objects.filter(nationality=nationality))
    last_names = list(LastName.objects.filter(nationality=nationality))

    if not first_names:  # If there are no first names for the nationality
        first_names = list(FirstName.objects.all())

    if not last_names:  # If there are no last names for the nationality
        last_names = list(LastName.objects.all())

    first_name = random.choice(first_names).name
    last_name = random.choice(last_names).name

    positions = Position.objects.all()
    position = random.choice(positions)

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

    today = datetime.now(timezone.utc)
    start_date = today - timedelta(days=33 * 365)  # 33 years ago
    end_date = today - timedelta(days=18 * 365)  # 18 years ago
    random_birth_date = datetime.fromtimestamp(random.randint(int(start_date.timestamp()), int(end_date.timestamp())))

    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        date_born=random_birth_date,
        position=position,
        team=Team.objects.first()  # Ensure you have a valid team
    )
    player.save()

    # Create PlayerAttribute instances for all attributes
    for attr_name, value in attributes.items():
        attr = Attribute.objects.get(name=attr_name)  # Get the Attribute instance
        PlayerAttribute.objects.create(player=player, attribute=attr, value=value)

    return player
