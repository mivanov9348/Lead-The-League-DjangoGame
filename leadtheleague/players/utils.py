import random
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
    player.save()

    # Записване на атрибути
    for attr_name, value in attributes.items():
        attr = Attribute.objects.get(name=attr_name)
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

    # Актуализиране на играчите с is_starting
    Player.objects.filter(team=team, is_starting=True).update(is_starting=False)
    starting_players = []
    for position, players in selected_players.items():
        for player in players:
            player.is_starting = True
            starting_players.append(player)

    # Bulk update на всички стартови играчи
    Player.objects.bulk_update(starting_players, ['is_starting'])

    TeamTactics.objects.create(team=team, tactic=tactic)

    return selected_players










def get_team_match_stats(userteam):
    return PlayerMatchStatistic.objects.filter(player__team=userteam).select_related('player')


# Основна информация за играча
def get_personal_player_data(player):
    return {
        "first_name": player.first_name,
        "last_name": player.last_name,
        "position": player.position,
        "nationality": player.nationality.name,  # Националност
        "age": player.age,
        "price": player.price,
        'is_starting': player.is_starting
    }


def get_player_attributes(player):
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.prefetch_related('attribute').all()}


def get_player_season_stats(player, season):
    # Извличаме статистики за сезона на играча за конкретния сезон
    season_stats = PlayerSeasonStatistic.objects.filter(player=player, season=season).select_related('statistic')

    stats_data = {}
    for stat in season_stats:
        stats_data[stat.statistic.name] = stat.value  # Добавяме стойностите на статистиките

    return stats_data


def get_player_season_stats_by_team(team, season):
    players = team.players.filter(is_active=True)

    team_stats_data = []

    for player in players:
        # Получаваме личната информация и статистиките за сезона
        player_data = get_player_data(player)
        player_stats = get_player_season_stats(player, season)

        # Съхраняваме данните за играча
        team_stats_data.append({
            "player_data": player_data,
            "stats": player_stats,
        })

    return team_stats_data


# full player data
def get_player_data(player):
    # Извличаме данните за играча с използване на select_related и prefetch_related
    player_data = Player.objects.select_related('position', 'team', 'nationality') \
        .prefetch_related('playerattribute_set__attribute', 'season_stats__statistic') \
        .get(id=player.id)

    # Извличаме атрибутите на играча като речник
    attributes = {attr.attribute.name: attr.value for attr in player_data.playerattribute_set.all()}

    # Извличаме сезонните статистики на играча
    season_stats = {stat.statistic.name: stat.value for stat in player_data.season_stats.all()}

    # Връщаме комбинираните данни
    return {
        'player': {
            'first_name': player_data.first_name,
            'last_name': player_data.last_name,
            'age': player_data.age,
            'position': player_data.position.position_name,
            'team': player_data.team.name,
            'nationality': player_data.nationality.name,
            'positionabbr': player_data.position.abbr,
            'nationalityabbr': player_data.nationality.abbr,
            'is_starting': player_data.is_starting
        },
        'attributes': attributes,
        'season_stats': season_stats,
    }


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
