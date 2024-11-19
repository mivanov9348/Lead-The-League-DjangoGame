from django.db import transaction
from fixtures.models import Fixture
from game.models import Season
from players.models import Player, PlayerMatchStatistic, Statistic, Position, PlayerSeasonStatistic
from players.utils import get_player_match_stats
from .models import Match, EventTemplate, Event, AttributeEventWeight, MatchEvent, EventResult
import random
from django.db.models import F, Q
from django.utils import timezone
from datetime import datetime
from teams.models import Team, TeamTactics


def generate_matches_for_season(season):
    fixtures = Fixture.objects.filter(season=season)

    for fixture in fixtures:
        Match.objects.create(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            division=fixture.division,
            match_date=fixture.date,  # Използваме match_date вместо date
            match_time=fixture.match_time,  # Използваме match_time вместо time
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


def get_user_today_match(user):
    today = timezone.now().date()
    user_team = Team.objects.get(user=user)

    next_match = Match.objects.filter(
        Q(home_team=user_team) | Q(away_team=user_team),
        match_date__gte=today
    ).first()

    return next_match


def get_match_status(match):
    current_time = timezone.now()

    if match.is_played:
        match_status = 'Ended'
    elif current_time < timezone.make_aware(datetime.combine(match.match_date, match.match_time)):
        match_status = 'Upcoming'
    else:
        match_status = 'LIVE'
    return match_status


def get_starting_lineup(team):
    try:
        team_tactics = TeamTactics.objects.get(team=team)
        starting_players = team_tactics.starting_players.all().order_by('position_id')
        return starting_players
    except TeamTactics.DoesNotExist:
        return Player.objects.none()  # Връща празен QuerySet ако няма намерен TeamTactics


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
    try:
        team_tactics = TeamTactics.objects.get(team=team)
        starting_player_ids = list(team_tactics.starting_players.values_list('id', flat=True))
        if starting_player_ids:
            selected_player_id = random.choice(starting_player_ids)
            selected_player = Player.objects.get(id=selected_player_id)
            return selected_player
        else:
            return None
    except TeamTactics.DoesNotExist:
        return None


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
    # Вземаме всички EventResults за дадения тип събитие и ги сортираме по `event_threshold` във възходящ ред
    event_results = EventResult.objects.filter(event_type__type=event_type).order_by('event_threshold')

    chosen_template = None
    # Обхождаме всеки EventResult и намираме първия съвпадащ EventTemplate
    for event_result in event_results:
        if success <= event_result.event_threshold:
            # Вземаме съответния EventTemplate за този EventResult
            chosen_template = EventTemplate.objects.filter(event_result=event_result).first()
            break  # Спряме се на първия валиден диапазон

    return chosen_template


# Getting needed players for this event
def get_event_players(template, main_player, team):
    num_players = template.num_players
    players = [main_player]

    if num_players == 2:
        # Избираме втори играч от отбора, като проверяваме да не е същия като основния играч
        while True:
            second_player = choose_event_random_player(team)
            if second_player != main_player:
                players.append(second_player)
                break

    return players


def fill_template_with_players(template, players):
    # Форматираме имената на играчите за използване в шаблона
    player_1_name = f"{players[0].first_name} {players[0].last_name} ({players[0].team.name})"
    player_2_name = f"{players[1].first_name} {players[1].last_name} ({players[1].team.name})" if len(
        players) > 1 else ""

    # Форматираме текста на шаблона, като заменяме player_1 и player_2 с реалните имена
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
    goalkeeper_position = Position.objects.get(name='Goalkeeper')
    opposing_goalkeeper = opponent_team.players.filter(position=goalkeeper_position).first()

    goalie_stats = get_player_match_stats(opposing_goalkeeper, match) if opposing_goalkeeper else None

    # Създаваме мапинг между полетата от шаблона и статистиките
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
            # Добавяме статистика за втори играч, ако е необходимо
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
                # Разпределяме стойността на статистиката за всеки играч
                for player in players:
                    stats_dict[player][stat_name] = stats_dict[player].get(stat_name, 0) + stat_value

    # Запазваме статистиките за играчите
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

    # Записваме статистиките за вратаря, ако има
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
    # Проверка дали всички елементи в 'players' са обекти от тип 'Player'
    if players and not all(isinstance(player, Player) for player in players):
        raise ValueError("Всички елементи в 'players' трябва да бъдат обекти от типа 'Player'.")

    try:
        # Създаваме запис за събитието в базата данни
        match_event = MatchEvent.objects.create(
            match=match,
            minute=minute,
            event_type=template.event_result.event_type.type,  # Вземаме типа на събитието от EventResult
            description=formattedText,
            is_negative_event=template.event_result.is_negative_event,  # Вземаме дали е негативно събитие
            possession_kept=template.event_result.possession_kept  # Вземаме дали е запазено притежанието на топката
        )

        # Ако има играчи, свързваме ги със събитието
        if players:
            match_event.players.set(players)

        # Записваме събитието
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
