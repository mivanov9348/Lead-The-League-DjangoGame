import random
from teams.models import TeamTactics, Tactics
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

def get_team_match_stats(userteam):
    return PlayerMatchStats.objects.filter(player__team=userteam).select_related('player', 'stats')

def get_player_data(player):
    # Build attributes dictionary from pre-fetched data
    attribute_values = {
        attr.attribute.name: attr.value
        for attr in player.playerattribute_set.all()
    }

    season_stats = player.playerseasonstats_set.first()
    stats_data = {}

    if season_stats:
        player_stats = season_stats.stats

        if player_stats:  # Check if player_stats is not None
            stats_data = {
                'matches_played': season_stats.matches_played,
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



import random

def auto_select_starting_lineup(team):
    if Player.objects.filter(team=team, is_starting=True).count() >= 11:
        return

    tactic = Tactics.objects.order_by('?').first()
    if not tactic:
        raise ValueError("Няма налични тактики в базата данни.")

    required_positions = {
        'GK': tactic.num_goalkeepers,
        'DF': tactic.num_defenders,
        'MF': tactic.num_midfielders,
        'ATT': tactic.num_forwards,
    }

    selected_players = {
        'GK': [],
        'DF': [],
        'MF': [],
        'ATT': [],
    }

    players = Player.objects.filter(team=team)

    for player in players:
        if player.position.abbr in required_positions:
            if len(selected_players[player.position.abbr]) < required_positions[player.position.abbr]:
                selected_players[player.position.abbr].append(player)

    Player.objects.filter(team=team, is_starting=True).update(is_starting=False)
    for position, players in selected_players.items():
        for player in players:
            player.is_starting = True
            player.save()

    TeamTactics.objects.create(team=team, tactic=tactic)

    return selected_players

def update_tactics(dummy_team, new_team):
    dummy_team_tactics = TeamTactics.objects.filter(team=dummy_team).first()

    if dummy_team_tactics:
        TeamTactics.objects.update_or_create(
            team=new_team,
            defaults={
                'tactic': dummy_team_tactics.tactic,
            }
        )
    pass