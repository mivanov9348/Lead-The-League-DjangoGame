from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core.utils.nationality_utils import get_all_nationalities
from players.utils.get_player_stats_utils import get_all_positions, get_average_player_rating_for_current_season, \
    get_player_team, get_player_season_stats
from teams.models import Team


def filter_players(queryset, filters):

    if filters.get('free_agents') == "1":
        queryset = queryset.filter(team_players=None)
    else:
        if filters.get('teams'):
            queryset = queryset.filter(team_players__team__id=filters['teams'])
        if filters.get('league'):
            queryset = queryset.filter(team_players__team__league_id=filters['league'])

    # Останалите филтри
    if filters.get('age_min'):
        queryset = queryset.filter(age__gte=filters['age_min'])
    if filters.get('age_max'):
        queryset = queryset.filter(age__lte=filters['age_max'])
    if filters.get('nationality'):
        queryset = queryset.filter(nationality__abbreviation=filters['nationality'])
    if filters.get('position'):
        queryset = queryset.filter(position__abbreviation=filters['position'])
    return queryset

def sort_players(queryset, sort_field, order):
    if order == 'desc':
        sort_field = f'-{sort_field}'
    return queryset.order_by(sort_field)

def paginate_queryset(queryset, page_number, per_page=30):
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


def players_context(players_page, paginator):
    teams = Team.objects.values_list('name', flat=True)
    nationalities = get_all_nationalities()
    positions = get_all_positions()

    context = {
        'player_data': [
            {
                "personal_info": {
                    "id": player.id,
                    "name": player.name,
                    "positionabbr": player.position.abbreviation if player.position else "N/A",
                    "nationalityabbr": player.nationality.abbreviation if player.nationality else "N/A",
                    "age": player.age,
                    "price": player.price,
                    'image': player.image.url if player.image else '',
                    'rating': get_average_player_rating_for_current_season(player),
                },
                "team_info": {
                    "team_name": get_player_team(player)['team_name'],
                },
                "season_stats": get_player_season_stats(player),
            }
            for player in players_page
        ],
        'pages': range(max(players_page.number - 2, 1), min(players_page.number + 3, paginator.num_pages + 1)),
        'current_page': players_page.number,
        'teams': teams,
        'nationalities': nationalities,
        'positions': positions,
    }

    return context