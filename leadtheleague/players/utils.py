import os
import random
import shutil
from .models import Player, FirstName, LastName, Nationality, Position, PositionAttribute, PlayerAttribute, \
    Attribute, PlayerSeasonStatistic, PlayerMatchStatistic
from teams.models import TeamPlayer, TeamTactics, Tactics


def calculate_player_price(player):
    GOALKEEPER_BASE_PRICE = 100000
    DEFENDER_BASE_PRICE = 120000
    MIDFIELDER_BASE_PRICE = 130000
    ATTACKER_BASE_PRICE = 150000
    DEFAULT_BASE_PRICE = 100000  # Default in case position does not match

    # Функцията за изчисляване на възрастовия фактор
    def get_age_factor(age):
        if age < 25:
            return 1.2
        elif age > 30:
            return 0.8
        return 1.0

    # Създаване на речник с базови цени
    base_prices = {
        'Goalkeeper': GOALKEEPER_BASE_PRICE,
        'Defender': DEFENDER_BASE_PRICE,
        'Midfielder': MIDFIELDER_BASE_PRICE,
        'Attacker': ATTACKER_BASE_PRICE
    }

    base_price = base_prices.get(player.position.name, DEFAULT_BASE_PRICE)
    age_factor = get_age_factor(player.age)
    total_attributes = sum(PlayerAttribute.objects.filter(player=player).values_list('value', flat=True))

    # Увеличаваме значението на атрибутите в крайната цена
    return int(base_price * age_factor + total_attributes * 10000)


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


def choose_random_photo(photo_folder):
    random_photo = random.choice(os.listdir(photo_folder))
    return os.path.join(photo_folder, random_photo)


def copy_player_image_to_static(photo_folder, player_id, static_path):
    chosen_photo = choose_random_photo(photo_folder)

    # Проверка дали избраната снимка съществува
    if not os.path.exists(chosen_photo):
        print(f"Файлът {chosen_photo} не съществува.")
        return None

    # Коректен път към новото място
    new_photo_path = os.path.join(static_path, 'playerimages', f"{player_id}.png")

    # Създаване на директорите, ако не съществуват
    os.makedirs(os.path.dirname(new_photo_path), exist_ok=True)

    # Копиране на файла
    shutil.copy(chosen_photo, new_photo_path)
    print(f"Копирана снимка от {chosen_photo} до: {new_photo_path}")
    return f'playerimages/{player_id}.png'


def generate_random_player(team=None, position=None):
    nationalities = Nationality.objects.all()
    positions = Position.objects.all()
    attributes = {attr.name: random.randint(1, 20) for attr in Attribute.objects.all()}
    nationality = random.choice(nationalities)
    region = nationality.region
    team_player_numbers = set(TeamPlayer.objects.filter(team=team).values_list('shirt_number', flat=True))

    first_name, last_name = get_random_name(region)
    if position is None:
        position = random.choice(positions)

    position_attributes = PositionAttribute.objects.filter(position=position)
    for pos_attr in position_attributes:
        if pos_attr.attribute.name in attributes:
            base_value = attributes[pos_attr.attribute.name]
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

    for attr_name, value in attributes.items():
        PlayerAttribute.objects.create(
            player=player,
            attribute=Attribute.objects.get(name=attr_name),
            value=value
        )

    player.price = calculate_player_price(player)
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    player.photo = copy_player_image_to_static("E:/Data/playersImages", player.id, static_path)

    while True:
        random_number = random.randint(1, 99)
        if random_number not in team_player_numbers:
            break

    player.save()

    if team:
        TeamPlayer.objects.create(player=player, team=team, shirt_number=random_number)

    return player


def generate_team_players(team):
    position_gk = Position.objects.get(name='Goalkeeper')
    position_def = Position.objects.get(name='Defender')
    position_mid = Position.objects.get(name='Midfielder')
    position_st = Position.objects.get(name='Attacker')

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


def auto_select_starting_lineup(team):
    # Проверяваме дали вече има избран стартов състав чрез TeamTactics
    team_tactics, created = TeamTactics.objects.get_or_create(team=team)
    if team_tactics.starting_players.count() >= 11:
        return

    tactic = Tactics.objects.order_by('?').first()
    if not tactic:
        raise ValueError("Няма налични тактики в базата данни.")

    required_positions = {
        'GK': tactic.num_goalkeepers,
        'DF': tactic.num_defenders,
        'MF': tactic.num_midfielders,
        'ATT': tactic.num_attackers,
    }

    selected_players = {
        'GK': [],
        'DF': [],
        'MF': [],
        'ATT': [],
    }

    # Вземаме подходящите играчи за отбора чрез `team_players` релацията
    players = Player.objects.filter(team_players__team=team)

    for player in players:
        if player.position.abbreviation in required_positions:
            if len(selected_players[player.position.abbreviation]) < required_positions[player.position.abbreviation]:
                selected_players[player.position.abbreviation].append(player)

    # Изчистване на предишните стартови играчи
    team_tactics.starting_players.clear()

    for position, players in selected_players.items():
        for player in players:
            team_tactics.starting_players.add(player)

    team_tactics.tactic = tactic
    team_tactics.save()

    return selected_players


def get_players_by_position(players, position):
    return [player for player in players if player['player_data']['player']['positionabbr'] == position]


def split_players_by_starting_status(players, team):
    try:
        team_tactics = TeamTactics.objects.get(team=team)
        starting_player_ids = set(team_tactics.starting_players.values_list('id', flat=True))
    except TeamTactics.DoesNotExist:
        starting_player_ids = set()

    startingPlayers = [player for player in players if player['player_data']['player']['id'] in starting_player_ids]
    reservePlayers = [player for player in players if player['player_data']['player']['id'] not in starting_player_ids]

    return startingPlayers, reservePlayers


def get_team_match_stats(userteam):
    return PlayerMatchStatistic.objects.filter(player__team=userteam).select_related('player')


# Основна информация за играча
def get_personal_player_data(player):
    player = Player.objects.select_related('nationality', 'position').get(id=player.id)
    return {
        'id': player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "position": player.position.name,
        "nationality": player.nationality.name,  # Националност
        "age": player.age,
        "price": player.price,
    }


def get_player_attributes(player):
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}


def get_player_season_stats(player, season):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player, season=season).select_related('statistic')
    stats_data = {stat.statistic.name: stat.value for stat in season_stats}
    return stats_data


def get_player_season_stats_by_team(team, season):
    players = Player.objects.filter(team=team, is_active=True).select_related('position',
                                                                              'nationality').prefetch_related(
        'playerattribute_set__attribute', 'season_stats__statistic')
    team_stats_data = []
    for player in players:
        player_data = get_personal_player_data(player)
        player_stats = get_player_season_stats(player, season)
        team_stats_data.append({
            "player_data": player_data,
            "stats": player_stats,
        })
    return team_stats_data


# full player data
def get_player_data(player):
    player = Player.objects.select_related('position', 'nationality').prefetch_related(
        'playerattribute_set__attribute', 'season_stats__statistic', 'team_players__team').get(id=player.id)
    player_data = {
        'player': get_personal_player_data(player),
        'attributes': get_player_attributes(player),
        'season_stats': {stat.statistic.name: stat.value for stat in player.season_stats.all()},
    }
    return player_data



def get_player_match_stats(player, match):
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match).select_related('statistic')
    stats_dict = {stat.statistic.name: stat.value for stat in stats}
    return stats_dict


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


def calculate_player_rating(player, match):
    stats = PlayerMatchStatistic.objects.filter(player=player, match=match)

    # Extract relevant statistics
    stats_dict = {stat.statistic.name: stat.value for stat in stats}

    # Default weights for each statistic
    weights = {
        'assists': 1.0,
        'cleanSheets': 1.5,
        'conceded': -1.0,
        'dribbles': 0.5,
        'fouls': -0.5,
        'goals': 2.0,
        'matches': 0.1,
        'minutesPlayed': 0.01,
        'passes': 0.2,
        'redCards': -2.0,
        'saves': 1.0,
        'shoots': 0.3,
        'shootsOnTarget': 0.5,
        'tackles': 0.3,
        'yellowCards': -0.5,
    }

    # Rating calculation
    rating = 5.0  # Start with a neutral base rating

    for stat, weight in weights.items():
        rating += stats_dict.get(stat, 0) * weight

    # Ensure the rating is between 1 and 10
    rating = max(1.0, min(10.0, rating))

    return rating

# Example usage:
# player_rating = calculate_player_rating(some_player, some_match)
# print(player_rating)
