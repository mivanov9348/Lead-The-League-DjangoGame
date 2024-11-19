import os
import random
import shutil
from leadtheleague import settings
from teams.models import TeamTactics, Tactics
from .models import Player, FirstName, LastName, Nationality, Position, PositionAttribute, PlayerAttribute, \
    Attribute, PlayerSeasonStatistic, PlayerMatchStatistic

def calculate_player_price(player):
    base_prices = {
        'Goalkeeper': 20000,
        'Defender': 30000,
        'Midfielder': 40000,
        'Attacker': 50000
    }

    base_price = base_prices.get(player.position.name, 2500)
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


def get_random_player_image():
    photo_folder = "E:/Data/playersImages"  # Път до папката със снимките
    photos = [f for f in os.listdir(photo_folder) if os.path.isfile(os.path.join(photo_folder, f))]
    if not photos:
        print("Грешка: Папката със снимки е празна или не съществува.")
        return None  # Ако папката е празна
    selected_photo = os.path.join(photo_folder, random.choice(photos))
    print(f"Избрана снимка: {selected_photo}")
    return selected_photo


def clear_player_images_folder():
    static_path = os.path.join(settings.STATICFILES_DIRS[0], "playersimages")
    if os.path.exists(static_path):
        shutil.rmtree(static_path)
        print(f"Изтрита папка: {static_path}")
    os.makedirs(static_path)
    print(f"Създадена нова папка: {static_path}")


def copy_player_image_to_static(photo_path, player_id):
    static_path = os.path.join(settings.STATICFILES_DIRS[0], "playersimages")
    new_photo_path = os.path.join(static_path, f"{player_id}.png")
    shutil.copy(photo_path, new_photo_path)
    print(f"Копирана снимка в: {new_photo_path}")
    return f'{player_id}.png'  # Връща само "id.png"


def generate_random_player(team=None, position=None):
    # Кешираме националностите и позициите
    nationalities = Nationality.objects.all()
    positions = Position.objects.all()
    attributes = {attr.name: random.randint(1, 20) for attr in Attribute.objects.all()}

    nationality = random.choice(nationalities)
    region = nationality.region
    first_name, last_name = get_random_name(region)

    # Ако позицията не е зададена, избираме случайна
    if position is None:
        position = random.choice(positions)

    # Извличаме атрибутите за позицията
    position_attributes = PositionAttribute.objects.filter(position=position)

    # Настройваме стойностите на атрибутите според важността
    for pos_attr in position_attributes:
        if pos_attr.attribute.name in attributes:
            base_value = attributes[pos_attr.attribute.name]
            boosted_value = min(int(base_value * (1 + (pos_attr.importance - 1) * 0.3)), 20)
            attributes[pos_attr.attribute.name] = boosted_value

    # Създаване на нов играч
    age = random.randint(18, 35)
    player = Player(
        first_name=first_name,
        last_name=last_name,
        nationality=nationality,
        age=age,
        position=position,
        team=team
    )

    print(f"Създаден играч: {player}")

    player.save()

    # Записване на атрибути
    for attr_name, value in attributes.items():
        attr = Attribute.objects.get(name=attr_name)
        PlayerAttribute.objects.create(player=player, attribute=attr, value=value)

    player.price = calculate_player_price(player)
    print(f"Изчислена цена на играча: {player.price}")

    # Изтриване на старата папка и създаване на нова
    clear_player_images_folder()

    photo_path = get_random_player_image()
    if photo_path:
        photo_file_name = copy_player_image_to_static(photo_path, player.id)
        player.photo = photo_file_name
        player.save()
        print(f"Записана снимка на играча: {player.photo}")
    else:
        print("Няма налична снимка за копиране.")

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

    players = Player.objects.filter(team=team)

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
    player = Player.objects.select_related('position', 'team', 'nationality').prefetch_related(
        'playerattribute_set__attribute', 'season_stats__statistic').get(id=player.id)
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
