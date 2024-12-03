from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Prefetch, QuerySet, Avg, Subquery, OuterRef, Case, When, Value, FloatField
from game.utils import get_current_season
from players.models import Player, PlayerSeasonStatistic, Position, Nationality, Attribute, PlayerMatchRating, \
    PlayerAttribute

STATISTICS_MAPPING = {
    'assists': 'assists',
    'cleanSheets': 'cleanSheets',
    'conceded': 'conceded',
    'dribbles': 'dribbles',
    'fouls': 'fouls',
    'goals': 'goals',
    'matches': 'matches',
    'minutesPlayed': 'minutesPlayed',
    'passes': 'passes',
    'redCards': 'redCards',
    'saves': 'saves',
    'shoots': 'shoots',
    'shootsOnTarget': 'shootsOnTarget',
    'tackles': 'tackles',
    'yellowCards': 'yellowCards',
    'price': 'price',
}

ATTRIBUTES_MAPPING = {
    'handling': 'handling',
    'reflexes': 'reflexes',
    'finishing': 'finishing',
    'shooting': 'shooting',
    'technique': 'technique',
    'passing': 'passing',
    'crossing': 'crossing',
    'tackling': 'tackling',
    'strength': 'strength',
    'determination': 'determination',
    'ballcontrol': 'ballcontrol',
    'dribbling': 'dribbling',
    'speed': 'speed',
    'vision': 'vision',
    'workrate': 'workrate',
    'stamina': 'stamina',
}


def filter_players(queryset, filters):
    team_filter = filters.get('team')
    age_min = filters.get('age_min')
    age_max = filters.get('age_max')
    nationality_filter = filters.get('nationality')
    position_filter = filters.get('position')

    if team_filter:
        queryset = queryset.filter(team_players__team__name=team_filter)
    if age_min:
        queryset = queryset.filter(age__gte=age_min)
    if age_max:
        queryset = queryset.filter(age__lte=age_max)
    if nationality_filter:
        queryset = queryset.filter(nationality__abbreviation=nationality_filter)
    if position_filter:
        queryset = queryset.filter(position__abbreviation=position_filter)

    return queryset

def sort_players(queryset, sort_by, order):
    if sort_by in STATISTICS_MAPPING:
        # Сортиране по статистики
        queryset = queryset.annotate(
            sort_value=Subquery(
                PlayerSeasonStatistic.objects.filter(
                    player=OuterRef('pk'),
                    statistic__name=STATISTICS_MAPPING[sort_by]
                ).values('value')[:1]
            )
        )
    elif sort_by in ATTRIBUTES_MAPPING:
        # Сортиране по атрибути
        queryset = queryset.annotate(
            sort_value=Subquery(
                PlayerAttribute.objects.filter(
                    player=OuterRef('pk'),
                    attribute_name=ATTRIBUTES_MAPPING[sort_by]
                ).values('value')[:1]
            )
        )
    else:
        return queryset  # Без промени, ако няма съвпадение

    # Обработка на празни стойности и прилагане на сортиране
    queryset = queryset.annotate(
        sort_value_cleaned=Case(
            When(sort_value__isnull=True, then=Value(0)),  # Заместване на null със стойност 0
            default='sort_value',
            output_field=FloatField()
        )
    )
    return queryset.order_by('-sort_value_cleaned' if order == 'desc' else 'sort_value_cleaned')



def paginate_queryset(queryset, page_number, items_per_page=20):
    paginator = Paginator(queryset, items_per_page)
    page = paginator.get_page(page_number)
    return page, paginator


def get_all_nationalities() -> QuerySet[Nationality]:
    """Retrieve all nationalities from the database."""
    return Nationality.objects.all()


def get_all_positions() -> QuerySet[Position]:
    """Retrieve all positions from the database."""
    return Position.objects.all()

def get_average_player_rating_for_current_season(player: Player) -> float:
    # Получаваме текущия сезон
    current_season = get_current_season()

    # Изчисляваме средния рейтинг за играча за текущия сезон
    average_rating = PlayerMatchRating.objects.filter(
        player=player,
        match__season=current_season  # Предполага се, че атрибутът 'season' е наличен
    ).aggregate(Avg('rating'))['rating__avg']

    return average_rating if average_rating is not None else 0.0

def get_attributes():
    attributes = cache.get('attributes')
    if not attributes:
        attributes = list(Attribute.objects.values_list('name', flat=True))
        cache.set('attributes', attributes, 3600)  # Кеширане за 1 час
    return attributes

def get_player_team(player):
    team_player = player.team_players.select_related('team').first()
    return {
        'team_name': team_player.team.name if team_player else 'No team',
        'shirt_number': team_player.shirt_number if team_player else None,
    }

def get_personal_player_data(player):
    return {
        'id': player.id,
        'name': player.name,
        'first_name': player.first_name,
        'last_name': player.last_name,
        'position': player.position.name if player.position else 'Unknown',
        'positionabbr': player.position.abbreviation if player.position else 'Unknown',
        'nationality': player.nationality.name if player.nationality else 'Unknown',
        'nationalityabbr': player.nationality.abbreviation if player.nationality else 'Unknown',
        'age': player.age,
        'price': player.price,
        'is_active': player.is_active,
        'is_youth': player.is_youth,
        'is_free_agent': player.is_free_agent,
    }

def get_player_attributes(player):
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}


def get_player_season_stats(player, season=None):
    query = player.season_stats.select_related('season', 'statistic')
    if season:
        query = query.filter(season=season)
    return {stat.statistic.name: stat.value for stat in query}

def get_player_season_stats_all_seasons(player):
    season_stats = PlayerSeasonStatistic.objects.filter(player=player).select_related('season', 'statistic')

    # Групираме статистиките по сезони
    all_stats = {}
    for stat in season_stats:
        season_number = stat.season.season_number
        if season_number not in all_stats:
            all_stats[season_number] = {}
        all_stats[season_number][stat.statistic.name] = stat.value

    return all_stats

def get_players_season_stats_by_team(team):
    players = team.team_players.select_related('player').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        )
    )
    player_data = {}
    for team_player in players:
        player = team_player.player
        season_stats = {
            stat.statistic.name: stat.value for stat in player.season_stats.all()
        }
        player_data[player.id] = {
            'personal_info': {
                'id': player.id,
                'name': player.name,
                'position': player.position.name if player.position else 'Unknown',
                'position_abbr': player.position.abbreviation if player.position else 'N/A',
                'nationality': player.nationality.name if player.nationality else 'Unknown',
                'nationality_abbr': player.nationality.abbreviation if player.nationality else 'N/A',
                'image_url': player.image.url if player.image else None,
            },
            'season_stats': season_stats,
        }
    return player_data

def get_player_data(player):
    return {
        'personal_info': get_personal_player_data(player),
        'attributes': get_player_attributes(player),
        'team_info': get_player_team(player),
        'stats': {
            'season_stats': get_player_season_stats(player),
            'match_stats': get_player_match_stats(player),
        },
    }

def get_player_match_stats(player, match=None):
    query = player.match_stats.select_related('match', 'statistic')
    if match:
        query = query.filter(match=match)
    match_stats = {}
    for stat in query:
        match_id = stat.match.id
        if match_id not in match_stats:
            match_stats[match_id] = {}
        match_stats[match_id][stat.statistic.name] = stat.value
    return match_stats

def get_all_free_agents():
    free_agents = Player.objects.filter(is_free_agent=True).prefetch_related('playerattribute_set__attribute')
    free_agents_data = []
    for player in free_agents:
        attributes = {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}
        free_agents_data.append({
            'id': player.id,
            'name': player.name,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'position': player.position.name if player.position else 'Unknown',
            'positionabbr': player.position.abbreviation if player.position else 'Unknown',
            'nationality': player.nationality.name if player.nationality else 'Unknown',
            'nationalityabbr': player.nationality.abbreviation if player.nationality else 'Unknown',
            'age': player.age,
            'price': player.price,
            'attributes': attributes,
            'image': player.image,
            'agent':player.agent
        })

    return free_agents_data