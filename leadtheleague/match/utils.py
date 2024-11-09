from django.db import transaction
from fixtures.models import Fixture
from game.models import Season
from players.models import Player, PlayerMatchStatistic, Statistic, Position, PositionAttribute, PlayerAttribute, \
    PlayerSeasonStatistic
from players.utils import get_player_match_stats
from .models import Match, EventTemplate, Event, AttributeEventWeight, MatchEvent
from datetime import datetime
import random
from freezegun import freeze_time
from django.utils import timezone
from django.db.models import F


def generate_matches_for_season(season):
    fixtures = Fixture.objects.filter(season=season)

    for fixture in fixtures:
        Match.objects.create(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            division=fixture.division,
            date=datetime.combine(fixture.date, fixture.match_time),
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        )


def update_matches(dummy_team, new_team):
    home_matches = Match.objects.filter(home_team=dummy_team)
    away_matches = Match.objects.filter(away_team=dummy_team)

    for match in home_matches:
        match.home_team = new_team
        match.save()

    for match in away_matches:
        match.away_team = new_team
        match.save()


@freeze_time("2024-11-07 11:00:00+00:00")
def get_match_status(match):
    current_time = timezone.now()

    if match.is_played:
        match_status = 'Ended'
    elif current_time < match.date:
        match_status = 'Upcoming'
    else:
        match_status = 'LIVE'
    return match_status


def get_lineup_data(players, match):
    return [
        {
            'player': player,
            'stats': get_player_match_stats(player, match)
        }
        for player in players
    ]


def update_match_minute(match):
    current_minute = match.current_minute

    # Увеличаваме минутата с произволно число между 1 и 5
    increment = random.randint(1, 7)
    current_minute += increment

    # Ако минутата е по-голяма от 90, я настройваме на 90
    if current_minute > 90:
        current_minute = 90

    # Записваме текущата минута и състоянието на мача в базата данни
    match.current_minute = current_minute
    match.save()

    return current_minute


def generate_player_match_stats():
    current_season = Season.objects.filter(is_ended=False).first()
    if not current_season:
        return

    matches = Match.objects.filter(season=current_season)
    players = Player.objects.all()

    for match in matches:
        for player in players:
            if player.team in [match.home_team, match.away_team]:
                for statistic in Statistic.objects.all():
                    PlayerMatchStatistic.objects.create(
                        player=player,
                        match=match,
                        statistic=statistic,
                        value=0
                    )


def get_match_team_initiative(match):
    return match.home_team if match.is_home_initiative else match.away_team


def choose_event_random_player(team):
    players = team.players.filter(is_starting=True)
    selected_player = random.choice(players)
    return selected_player


def get_random_event():
    event = Event.objects.exclude(type='Team')
    return random.choice(event)


def get_event_attributes_weight(event, player_attributes):
    weights = AttributeEventWeight.objects.filter(event=event)
    attributes_and_weights = []

    for weight in weights:
        attribute_value = player_attributes.get(weight.attribute)
        if attribute_value is not None:
            attributes_and_weights.append((attribute_value, weight.weight))
    return attributes_and_weights


def calculate_success_rate(event, attributes_and_weights):
    base_success = event.success_rate

    for attribute_value, weight in attributes_and_weights:
        base_success += (attribute_value * weight)

    return round(base_success, 2)


def get_event_template(event_type, success):
    # Вземаме всички темплейти от дадения тип и ги сортираме по `event_threshold` във възходящ ред
    event_templates = EventTemplate.objects.filter(event_type=event_type).order_by('event_threshold')

    chosen_template = None
    # Обхождаме всеки темплейт и запазваме този, който покрива текущата стойност на успеха
    for template in event_templates:
        if success <= template.event_threshold:
            chosen_template = template
            break  # Спряме се на първия валиден диапазон

    return chosen_template


# Getting needed players for this event
def get_event_players(template, main_player, team):
    num_players = template.num_players
    players = [main_player]

    if num_players == 2:
        while True:
            second_player = choose_event_random_player(team)
            if second_player != main_player:
                players.append(second_player)
                break

    return players


def get_team_template(match):
    event_result = ""
    if match.current_minute <= 1:
        event_result = "Kick Off"

    elif match.current_minute >= 45 <= match.current_minute < 46:
        match.current_minute = 45
        match.save()
        event_result = "Half-Time"

    elif match.current_minute >= 90:
        match.current_minute = 90
        match.save()
        event_result = "Full-Time"

    templates = EventTemplate.objects.filter(event_result=event_result)
    if templates.exists():
        return random.choice(templates)  # Връща произволен темплейт от наличните
    return None


def fill_template_with_players(template, players):
    player_1_name = f"{players[0].first_name} {players[0].last_name} ({players[0].team.name})"
    player_2_name = f"{players[1].first_name} {players[1].last_name} ({players[1].team.name}" if len(
        players) > 1 else ""

    formatted_text = template.template_text.format(
        player_1=player_1_name,
        player_2=player_2_name
    )

    return formatted_text


def update_player_stats_from_template(match, template, players):
    stats_dict = {}

    # Вземаме статистиките за всеки играч в списъка
    for player in players:
        stats_dict[player] = get_player_match_stats(player, match)

    # Намираме противниковия отбор
    opponent_team = match.away_team if players[0].team == match.home_team else match.home_team

    # Откриваме вратаря на противниковия отбор
    goalkeeper_position = Position.objects.get(position_name='Goalkeeper')
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

    # Записване на статистиките от шаблона
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

    # Запазване на статистиките
    for player, stats in stats_dict.items():
        for stat_name, value in stats.items():
            player_stat, created = PlayerMatchStatistic.objects.get_or_create(
                player=player,
                match=match,
                statistic__name=stat_name,
                defaults={'value': 0}
            )
            player_stat.value = value
            player_stat.save()

    if opposing_goalkeeper and goalie_stats:
        for stat_name, value in goalie_stats.items():
            player_stat, created = PlayerMatchStatistic.objects.get_or_create(
                player=opposing_goalkeeper,
                match=match,
                statistic__name=stat_name,
                defaults={'value': 0}
            )
            player_stat.value = value
            player_stat.save()


def update_matchscore(template, match, team_with_initiative):
    if hasattr(template, 'goals') and template.goals > 0:
        if team_with_initiative == match.home_team:
            match.home_goals += 1
        else:
            match.away_goals += 1
    match.save()


def log_match_event(match, minute, template, formattedText, players=None):
    # Проверка дали всички елементи в 'players' са обекти от тип 'Player'
    if players and not all(isinstance(player, Player) for player in players):
        raise ValueError("Всички елементи в 'players' трябва да бъдат обекти от типа 'Player'.")

    try:
        # Създаване на запис за събитието
        match_event = MatchEvent.objects.create(
            match=match,
            minute=minute,
            event_type=template.event_type.type,
            description=formattedText,
            is_negative_event=template.is_negative_event,
            possession_kept=template.possession_kept
        )

        # Записване на играчите, свързани със събитието, само ако има такива
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


def finalize_match(match):
    match.is_played = True
    match.save()
    # Взимаме статистиките на играчите за този мач
    player_match_stats = PlayerMatchStatistic.objects.filter(match=match)

    with transaction.atomic():
        for match_stat in player_match_stats:
            # Намираме съществуващата сезонна статистика и я обновяваме
            season_stat, created = PlayerSeasonStatistic.objects.get_or_create(
                player=match_stat.player,
                statistic=match_stat.statistic,
                season=match.season,
                defaults={'value': 0}
            )

            season_stat.value = F('value') + match_stat.value
            season_stat.save()
