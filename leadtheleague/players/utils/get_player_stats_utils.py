from collections import defaultdict

from game.utils import get_current_season
from players.models import PlayerMatchStatistic, Player, PlayerSeasonStatistic


def get_personal_player_data(player):
    """
    Връща основната персонална информация за един играч.
    """
    return {
        'id': player.id,
        'name': player.name,
        'first_name': player.first_name,
        'last_name': player.last_name,
        'position': player.position.name if player.position else 'Unknown',
        'nationality': player.nationality.name if player.nationality else 'Unknown',
        'age': player.age,
        'price': player.price,
        'is_active': player.is_active,
        'is_youth': player.is_youth,
        'is_free_agent': player.is_free_agent,
    }


def get_player_attributes(player):
    """
    Връща атрибутите на даден играч.
    """
    player = Player.objects.prefetch_related('playerattribute_set__attribute').get(id=player.id)
    return {attr.attribute.name: attr.value for attr in player.playerattribute_set.all()}


def get_player_season_stats(player):
    """
    Метод за извличане на всички статистики на играча за конкретен сезон.

    :param season: Сезонът, за който ще се вземат статистиките.
    :return: Списък със статистики на играча за избрания сезон.
    """
    season = get_current_season()

    # Вземаме статистиките на играча за конкретния сезон
    player_stats = PlayerSeasonStatistic.objects.filter(
        player=player,
        season=season
    ).select_related('statistic')  # Използваме select_related за по-ефективно извличане на свързаните статистики

    return player_stats


def get_player_team_info(player):
    """
    Връща информация за отбора на играча и номера на фланелката.
    """
    player = Player.objects.prefetch_related('team_players__team').get(id=player.id)
    team_player = player.team_players.first()  # Взима първия запис от TeamPlayer
    return {
        'team_name': team_player.team.name if team_player else 'No team',
        'shirt_number': team_player.shirt_number if team_player else None,
    }


def get_player_data(player):
    """
    Връща пълната информация за даден играч.
    """
    personal_info = get_personal_player_data(player)
    attributes = get_player_attributes(player)
    team_info = get_player_team_info(player)
    season_stats = get_player_season_stats(player)
    match_stats = get_player_match_stats(player)

    return {
        'personal_info': personal_info,
        'attributes': attributes,
        'team_info': team_info,
        'stats': {
            'season_stats': season_stats,
            'match_stats': match_stats,
        },
    }


def get_player_match_stats(player):
    """
    Връща статистиката на играч за всеки мач.
    """
    match_stats = PlayerMatchStatistic.objects.filter(player_id=player.id).select_related('statistic', 'match')
    return {f"Match {stat.match.id}: {stat.statistic.name}": stat.value for stat in match_stats}
