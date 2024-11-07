from tempfile import template

from fixtures.models import Fixture
from game.models import Season
from players.models import Player, PlayerMatchStatistic, Statistic, Position, PositionAttribute, PlayerAttribute
from players.utils import get_player_match_stats
from .models import Match, EventTemplate, Event, AttributeEventWeight
from datetime import datetime
import random


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


def get_current_minute(request):
    current_minute = request.session.get('current_minute', 0)
    increment = random.randint(1, 5)
    current_minute += increment

    if current_minute > 90:
        current_minute = 90

    return current_minute


def generate_player_match_stats():
    current_season = Season.objects.filter(is_ended=False).first()  # Вземете първия несвършен сезон
    if not current_season:
        print("Няма активен сезон.")
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
    event = Event.objects.all()
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

def fill_template_with_players(template, main_player, team):
    num_players = template.num_players

    players = {"player_1": main_player}

    if num_players == 2:
        while True:
            second_player = choose_event_random_player(team)
            if second_player != main_player:
                players["player_2"] = second_player
                break

    formatted_text = template.template_text.format(
        player_1=f"{players['player_1'].first_name} {players['player_1'].last_name}",
        player_2=f"{players.get('player_2', '').first_name} {players.get('player_2', '').last_name}" if players.get(
            "player_2") else ""
    )

    return formatted_text


def update_player_stats_from_template(player, match, template, player_2=None):
    print(f"Updating stats for player: {player}, match: {match}, template: {template}, player_2: {player_2}")

    # Взимаме текущата статистика на играча за мача
    stats = get_player_match_stats(player, match)

    stats_2 = get_player_match_stats(player_2, match) if player_2 else None

    # Намираме противниковия отбор, използвайки home_team и away_team
    opponent_team = match.away_team if player.team == match.home_team else match.home_team

    # Откриваме вратаря на противниковия отбор
    goalkeeper_position = Position.objects.get(position_name='Goalkeeper')
    opposing_goalkeeper = opponent_team.players.filter(position=goalkeeper_position).first()

    goalie_stats = get_player_match_stats(opposing_goalkeeper, match) if opposing_goalkeeper else None
    if opposing_goalkeeper:
        print(f"Goalkeeper stats: {goalie_stats}")

    # Свързваме полетата от шаблона с имената на статистиките
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
        stat_value = getattr(template, field)

        # Проверяваме за голямо значение (като 1, за да има ефект)
        if stat_value > 0:
            if stat_name == "assists" and player_2:
                # Асистенцията се записва на втория играч (player_2)
                if stats_2 and "assists" in stats_2:
                    stats_2["assists"] += stat_value
                elif stats_2:
                    stats_2["assists"] = stat_value
            elif stat_name == "passes" and player_2:
                # За паса добавяме само на подаващия, без ефект върху получателя
                if stats and "passes" in stats:
                    stats["passes"] += stat_value
                else:
                    stats["passes"] = stat_value
            elif stat_name == "conceded" and opposing_goalkeeper:
                # Допуснат гол се записва на вратаря на противниковия отбор
                if goalie_stats and "conceded" in goalie_stats:
                    goalie_stats["conceded"] += stat_value
                elif goalie_stats:
                    goalie_stats["conceded"] = stat_value
            else:
                # Добавяме стойността към главния играч
                if stat_name in stats:
                    stats[stat_name] += stat_value
                else:
                    stats[stat_name] = stat_value

    # Запазваме промените за главния играч
    for stat_name, value in stats.items():

        try:
            player_stat, created = PlayerMatchStatistic.objects.get_or_create(
                player=player,
                match=match,
                statistic__name=stat_name
            )
            player_stat.value = value
            player_stat.save()
        except Exception as e:
            print(f"Error saving stat for player {player.id}: {stat_name} - {e}")

    # Запазваме промените за втория играч (ако има)
    if player_2 and stats_2:
        for stat_name, value in stats_2.items():
            try:
                player_stat, created = PlayerMatchStatistic.objects.get_or_create(
                    player=player_2,
                    match=match,
                    statistic__name=stat_name
                )
                player_stat.value = value
                player_stat.save()
            except Exception as e:
                print(f"Error saving stat for player_2 {player_2.id}: {stat_name} - {e}")

    # Запазваме промените за вратаря на противника (ако има)
    if opposing_goalkeeper and goalie_stats:
        for stat_name, value in goalie_stats.items():
            try:
                player_stat, created = PlayerMatchStatistic.objects.get_or_create(
                    player=opposing_goalkeeper,
                    match=match,
                    statistic__name=stat_name
                )
                player_stat.value = value
                player_stat.save()
            except Exception as e:
                print(f"Error saving stat for goalkeeper {opposing_goalkeeper.id}: {stat_name} - {e}")
