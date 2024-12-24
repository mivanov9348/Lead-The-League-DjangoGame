from random import random
from django.db import transaction
from django.db.models import F
from match.models import MatchEvent
from players.models import Player, PlayerMatchStatistic, PlayerSeasonStatistic, Position
from players.utils.get_player_stats_utils import get_player_match_stats
from teams.models import TeamTactics


def choose_event_random_player(team):
    try:
        team_tactics = TeamTactics.objects.select_related('teams').get(team=team)
        starting_player_ids = list(team_tactics.starting_players.values_list('id', flat=True))
        if starting_player_ids:
            selected_player_id = random.choice(starting_player_ids)
            selected_player = Player.objects.get(id=selected_player_id)
            return selected_player
        else:
            return None
    except TeamTactics.DoesNotExist:
        return None


def update_match_minute(match):
    current_minute = match.current_minute

    increment = random.randint(1, 7)
    current_minute += increment

    if current_minute > 90:
        current_minute = 90

    match.current_minute = current_minute
    match.save()

    return current_minute


def get_match_team_initiative(match):
    return match.home_team if match.is_home_initiative else match.away_team


def finalize_match(match):
    match.is_played = True
    match.save()
    player_match_stats = PlayerMatchStatistic.objects.filter(match=match)

    with transaction.atomic():
        season_stats_list = []
        for match_stat in player_match_stats:
            season_stat, created = PlayerSeasonStatistic.objects.get_or_create(
                player=match_stat.player,
                statistic=match_stat.statistic,
                season=match.season,
                defaults={'value': 0}
            )

            season_stat.value = F('value') + match_stat.value
            season_stats_list.append(season_stat)

        PlayerSeasonStatistic.objects.bulk_update(season_stats_list, ['value'])


def update_player_stats_from_template(match, template, players):
    stats_dict = {player: get_player_match_stats(player, match) for player in players}

    opponent_team = match.away_team if players[0].team == match.home_team else match.home_team

    goalkeeper_position = Position.objects.get(name='Goalkeeper')
    opposing_goalkeeper = opponent_team.players.filter(position=goalkeeper_position).first()

    goalie_stats = get_player_match_stats(opposing_goalkeeper, match) if opposing_goalkeeper else None

    event_fields_to_stats = {
        "goals": "goals",
        "assists": "assists",
        "shoots": "shoots",
        "shootsOnTarget": "shootsOnTarget",
        "saves": "saves",
        "passes": "passes",
        "tackles": "tackles",
        "fouls": "fouls",
        "dribbles": "dribbles",
        "yellowCards": "yellowCards",
        "redCards": "redCards",
        "conceded": "conceded"
    }

    for field, stat_name in event_fields_to_stats.items():
        stat_value = getattr(template, field, 0)

        if stat_value > 0:
            if stat_name == "assists" and len(players) > 1:
                player_2 = players[1]
                stats_dict[player_2]["assists"] = stats_dict[player_2].get("assists", 0) + stat_value
            elif stat_name == "passes" and len(players) > 1:
                stats_dict[players[0]]["passes"] = stats_dict[players[0]].get("passes", 0) + stat_value
            elif stat_name == "conceded" and opposing_goalkeeper:
                goalie_stats["conceded"] = goalie_stats.get("conceded", 0) + stat_value
            elif stat_name == "goals":
                stats_dict[players[0]]["goals"] = stats_dict[players[0]].get("goals", 0) + stat_value
            else:
                for player in players:
                    stats_dict[player][stat_name] = stats_dict[player].get(stat_name, 0) + stat_value

    player_stats_list = []
    for player, stats in stats_dict.items():
        for stat_name, value in stats.items():
            player_stat = PlayerMatchStatistic.objects.get_or_create(
                player=player,
                match=match,
                statistic__name=stat_name,
                defaults={'value': 0}
            )
            player_stat.value = value
            player_stats_list.append(player_stat)

    PlayerMatchStatistic.objects.bulk_update(player_stats_list, ['value'])

    if opposing_goalkeeper and goalie_stats:
        goalie_stats_list = []
        for stat_name, value in goalie_stats.items():
            player_stat = PlayerMatchStatistic.objects.get_or_create(
                player=opposing_goalkeeper,
                match=match,
                statistic__name=stat_name,
                defaults={'value': 0}
            )
            player_stat.value = value
            goalie_stats_list.append(player_stat)

        PlayerMatchStatistic.objects.bulk_update(goalie_stats_list, ['value'])


def update_matchscore(template, match, team_with_initiative):
    # Проверяваме дали шаблонът съдържа полето "goals" и дали има стойност по-голяма от 0
    if hasattr(template.event_result, 'goals') and template.event_result.goals > 0:
        # Ако отбора с инициатива е домашен, увеличаваме головете на домашния отбор
        if team_with_initiative == match.home_team:
            match.home_goals += 1
        else:
            # Ако отбора с инициатива е гост, увеличаваме головете на гостувания отбор
            match.away_goals += 1
        match.save()


def log_match_event(match, minute, template, formattedText, players=None):
    if players and not all(isinstance(player, Player) for player in players):
        raise ValueError("Всички елементи в 'players' трябва да бъдат обекти от типа 'Player'.")

    try:
        match_event = MatchEvent.objects.create(
            match=match,
            minute=minute,
            event_type=template.event_result.event_type.type,  # Вземаме типа на събитието от EventResult
            description=formattedText,
            is_negative_event=template.event_result.is_negative_event,  # Вземаме дали е негативно събитие
            possession_kept=template.event_result.possession_kept  # Вземаме дали е запазено притежанието на топката
        )

        if players:
            match_event.players.set(players)

        match_event.save()

    except Exception as e:
        print(f'Error: {e}')


def check_initiative(template, match):
    if template.possession_kept:
        print("Инициативата се запазва.")
    else:
        # Смяна на инициативата
        match.is_home_initiative = not match.is_home_initiative
        match.save()


def fill_template_with_players(template, players):
    player_1_name = f"{players[0].first_name} {players[0].last_name} ({players[0].team.name})"
    player_2_name = f"{players[1].first_name} {players[1].last_name} ({players[1].team.name})" if len(
        players) > 1 else ""

    formatted_text = template.template_text.format(
        player_1=player_1_name,
        player_2=player_2_name
    )

    return formatted_text
