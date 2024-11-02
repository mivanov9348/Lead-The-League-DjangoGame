import random
from .models import Player, FirstName, LastName, Team, Nationality, Position, PositionAttribute, PlayerAttribute, \
    Attribute, PlayerSeasonStats, PlayerMatchStats


def calculate_player_price(player):

    player_data = get_player_data(player)

    base_prices = {
        'Goalkeeper': 20000,
        'Defender': 30000,
        'Midfielder': 40000,
        'Attacker': 50000
    }

    base_price = base_prices.get(player.position.position_name, 2500)
    age_factor = 1.2 if player.age < 25 else 0.8 if player.age > 30 else 1.0

    total_attributes = sum(PlayerAttribute.objects.filter(player=player).values_list('value', flat=True))
    return int(base_price * age_factor + total_attributes * 100)

def get_random_name(region):
    first_names = list(FirstName.objects.filter(region=region))
    last_names = list(LastName.objects.filter(region=region))

    if not first_names:
        first_names = list(FirstName.objects.all())

    if not last_names:
        last_names = list(LastName.objects.all())

    first_name = random.choice(first_names).name
    last_name = random.choice(last_names).name
    return first_name, last_name

def generate_random_player(team=None, position=None):
    nationalities = Nationality.objects.all()
    nationality = random.choice(nationalities)

    region = nationality.region

    first_name, last_name = get_random_name(region)

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

    age = random.randint(18, 35)

    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age=age,
        position=position,
        team=team
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

#
# def add_goal(player_id, season_id):
#     player_stats = PlayerSeasonStats.objects.get(player_id=player_id, season_id=season_id)
#     player_stats.stats.goals += 1
#     player_stats.stats.save()
#
#
# def add_assists(player_id, season_id):
#     player_stats = PlayerSeasonStats.objects.get(player_id=player_id, season_id=season_id)
#     player_stats.stats.assists += 1  # Достъп до PlayerStats чрез stats
#     player_stats.stats.save()
#
#
# def match_participate(player_id, season_id):
#     player_stats = PlayerSeasonStats.objects.get(player_id=player_id, season_id=season_id)
#     player_stats.matches_played += 1  # Променете matches на matches_played
#     player_stats.save()
#
#
# def goal_conceded(player_id, season_id):
#     player_stats = PlayerSeasonStats.objects.get(player_id=player_id, season_id=season_id)
#     player_stats.stats.conceded += 1  # Достъп до PlayerStats чрез stats
#     player_stats.stats.save()

def get_team_match_stats(userteam):
    return PlayerMatchStats.objects.filter(player__team=userteam).select_related('player', 'stats')

def get_player_data(player):
    attributes = PlayerAttribute.objects.filter(player=player)
    attribute_values = {attr.attribute.name: attr.value for attr in attributes}

    # Fetch the player's season stats
    season_stats = PlayerSeasonStats.objects.filter(player=player).first()
    stats_data = {}

    if season_stats:
        player_stats = season_stats.stats

        if player_stats:  # Ensure player_stats is not None
            stats_data = {
                'matches_played': season_stats.matches_played,  # Include matches_played here
                'goals': player_stats.goals,
                'assists': player_stats.assists,
                'shots': player_stats.shots,
                'shots_on_target': player_stats.shots_on_target,
                'passes': player_stats.passes,
                'dribbles': player_stats.dribbles,
                'tackles': player_stats.tackles,
                'yellow_cards': player_stats.yellow_cards,
                'red_cards': player_stats.red_cards,
                'minutes_played': player_stats.minutes_played,
                'saves': player_stats.saves,
                'clean_sheets': player_stats.clean_sheets,
                'conceded': player_stats.conceded,
            }

    return {
        'player': player,
        'attributes': attribute_values,
        'season_stats': stats_data,
    }

