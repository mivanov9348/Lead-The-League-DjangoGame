import random
from django.db import transaction
from match.models import MatchEvent, Event, AttributeEventWeight, EventResult, EventTemplate
from players.models import Player, Position, Statistic, PlayerMatchStatistic
from teams.models import TeamTactics, Team


def choose_event_random_player(team):
    try:
        team_tactics = TeamTactics.objects.select_related('team').get(team=team)
        starting_player = team_tactics.starting_players.order_by('?').first()
        return starting_player
    except TeamTactics.DoesNotExist:
        return None


def update_match_minute(match):
    increment = random.randint(1, 7)
    match.current_minute = min(match.current_minute + increment, 90)
    return match.current_minute

def get_match_team_initiative(match):
    return match.home_team if match.is_home_initiative else match.away_team

def finalize_match(match):
    with transaction.atomic():
        match.is_played = True
        match.save()

        fixture = match.fixture
        if not fixture:
            raise ValueError("Мачът няма свързан fixture.")

        fixture.home_goals = match.home_goals
        fixture.away_goals = match.away_goals
        fixture.is_finished = True

        if match.home_goals > match.away_goals:
            fixture.winner = match.home_team
        elif match.away_goals > match.home_goals:
            fixture.winner = match.away_team
        else:
            fixture.winner = None  # Равен резултат

        fixture.save()

    print(f"Match finalized: {match}. Fixture updated.")


def update_player_stats_from_template(match, template, players):
    if not players:
        raise ValueError("Не са подадени играчи за актуализиране на статистики.")

    with transaction.atomic():
        stats_dict = {player: {} for player in players}
        opponent_team = match.away_team if players[0].team == match.home_team else match.home_team
        goalkeeper_position = Position.objects.get(name='Goalkeeper')
        opposing_goalkeeper = opponent_team.players.filter(position=goalkeeper_position).first()
        goalie_stats = {} if opposing_goalkeeper else None

        event_fields_to_stats = {
            "goals": "Goals",
            "assists": "Assists",
            "shoots": "Shoots",
            "shootsOnTarget": "ShootsOnTarget",
            "saves": "Saves",
            "passes": "Passes",
            "tackles": "Tackles",
            "fouls": "Fouls",
            "dribbles": "Dribbles",
            "yellowCards": "YellowCards",
            "redCards": "RedCards",
            "conceded": "Conceded"
        }

        for field, stat_name in event_fields_to_stats.items():
            stat_value = getattr(template, field, 0)
            if stat_value > 0:
                if stat_name == "Conceded" and opposing_goalkeeper:
                    goalie_stats[stat_name] = goalie_stats.get(stat_name, 0) + stat_value
                elif stat_name in ["Assists", "Passes"] and len(players) > 1:
                    stats_dict[players[1]][stat_name] = stats_dict[players[1]].get(stat_name, 0) + stat_value
                else:
                    for player in players:
                        stats_dict[player][stat_name] = stats_dict[player].get(stat_name, 0) + stat_value

        # Bulk create or update player stats
        player_stats_list = []
        for player, stats in stats_dict.items():
            for stat_name, value in stats.items():
                stat_obj = Statistic.objects.get(name=stat_name)
                player_stat, _ = PlayerMatchStatistic.objects.get_or_create(
                    player=player,
                    match=match,
                    statistic=stat_obj,
                    defaults={'value': 0}
                )
                player_stat.value = value
                player_stats_list.append(player_stat)

        PlayerMatchStatistic.objects.bulk_update(player_stats_list, ['value'])

        # Update goalkeeper stats if applicable
        if opposing_goalkeeper and goalie_stats:
            goalie_stats_list = []
            for stat_name, value in goalie_stats.items():
                stat_obj = Statistic.objects.get(name=stat_name)
                player_stat, _ = PlayerMatchStatistic.objects.get_or_create(
                    player=opposing_goalkeeper,
                    match=match,
                    statistic=stat_obj,
                    defaults={'value': 0}
                )
                player_stat.value = value
                goalie_stats_list.append(player_stat)

            PlayerMatchStatistic.objects.bulk_update(goalie_stats_list, ['value'])


def update_match_score(template, match, team_with_initiative):
    if hasattr(template.event_result, 'goals') and template.event_result.goals > 0:
        if team_with_initiative == match.home_team:
            match.home_goals += 1
        else:
            match.away_goals += 1
        match.save()


def log_match_event(match, minute, template, formatted_text, players=None):
    if players and not all(isinstance(player, Player) for player in players):
        raise ValueError("Всички елементи в 'players' трябва да бъдат обекти от типа 'Player'.")

    try:
        with transaction.atomic():
            match_event_data = {
                "match": match,
                "minute": minute,
                "event_type": template.event_result.event_type.type,
                "description": formatted_text,
                "is_negative_event": template.event_result.is_negative_event,
                "possession_kept": template.event_result.possession_kept,
            }

            match_event = MatchEvent.objects.create(**match_event_data)

            if players:
                match_event.players.set(players)

            print(f"Успешно добавено събитие: {formatted_text} на минута {minute}.")
    except AttributeError as e:
        raise ValueError(f"Шаблонът за събитие е невалиден: {e}")
    except Exception as e:
        print(f"Грешка при логване на събитие: {e}")


def check_initiative(template, match):
    if template.possession_kept:
        print("The initiative saved")
    else:
        match.is_home_initiative = not match.is_home_initiative
        match.save()


def fill_template_with_players(template, players):
    player_1_name = f"{players[0].first_name} {players[0].last_name} ({players[0].team.name})"
    player_2_name = (
        f"{players[1].first_name} {players[1].last_name} ({players[1].team.name})" if len(players) > 1 else ""
    )

    formatted_text = template.template_text.format(
        player_1=player_1_name,
        player_2=player_2_name
    )
    return formatted_text


def get_random_match_event():
    return Event.objects.exclude(type='Team').only('id', 'type').order_by('?').first()

def get_match_event_attributes_weight(event, player_attributes):
    weights = AttributeEventWeight.objects.filter(event=event).only('attribute', 'weight')

    attributes_and_weights = [
        (player_attributes.get(weight.attribute), weight.weight)
        for weight in weights if weight.attribute in player_attributes
    ]
    return attributes_and_weights

def get_event_success_rate(event, attributes_and_weights):
    return round(
        event.success_rate + sum(attribute_value * weight for attribute_value, weight in attributes_and_weights), 2
    )

def get_match_event_template(event_type, success):
    event_results = EventResult.objects.filter(event_type__type=event_type).only('event_threshold')
    for event_result in event_results:
        if success <= event_result.event_threshold:
            return EventTemplate.objects.filter(event_result=event_result).select_related('event_result').only('id').first()
    return None

def get_event_players(template, main_player, team):
    players = [main_player]
    if template.num_players == 2:
        players.extend(
            team.players.exclude(id=main_player.id).only('id').order_by('?')[:1]
        )
    return players