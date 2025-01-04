import random

from django.db import transaction
from django.db.models import Q
from match.models import MatchEvent, Event, AttributeEventWeight, EventResult, EventTemplate
from players.models import Player, Position, Statistic, PlayerMatchStatistic
from teams.models import TeamTactics, Team, TeamPlayer

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


def update_player_stats_from_template(match, template, player):
    if not player:
        raise ValueError("No player provided for statistics update.")

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
        "conceded": "Conceded",
    }

    with transaction.atomic():
        player_stat, created = PlayerMatchStatistic.objects.get_or_create(
            player=player,
            match=match,
            defaults={"statistics": {stat: 0 for stat in event_fields_to_stats.values()}}
        )

        updated_stats = player_stat.statistics
        for field, stat_name in event_fields_to_stats.items():
            stat_value = getattr(template.event_result, field, 0)
            if stat_value > 0:
                updated_stats[stat_name] = updated_stats.get(stat_name, 0) + stat_value

        player_stat.statistics = updated_stats
        player_stat.save()

        print(f"Updated statistics for player {player.first_name} {player.last_name}.")


def update_match_score(event_result, match, team_with_initiative):
    import logging

    logging.basicConfig(
        filename='match_update.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Processing Event Result: {event_result.event_type} with result '{event_result.event_result}'")

    goal_events = {"ShotGoal", "CornerGoal", "FreeKickGoal", "PenaltyGoal"}

    if event_result.event_result in goal_events:
        logging.info(f'ev: ev.ev: {event_result} ---- {event_result.event_result}')
        if team_with_initiative == match.home_team:
            match.home_goals += 1
            logging.info(f"Goal for home team: {match.home_team}. New score: {match.home_goals}-{match.away_goals}")
        else:
            match.away_goals += 1
            logging.info(f"Goal for away team: {match.away_team}. New score: {match.home_goals}-{match.away_goals}")

        match.save()
        logging.info(f"Match score updated and saved. Match ID: {match.id}")
    else:
        logging.warning(f"No goal scored. Event: {event_result.event_result}")


def log_match_event(match, minute, template, formatted_text, player=None):
    if not player:
        raise ValueError("No player provided!")

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

            if player:
                match_event.players.add(player)

            print(f"Event successfully logged: {formatted_text} at minute {minute}.")
    except AttributeError as e:
        raise ValueError(f"Invalid template or event result: {e}")
    except Exception as e:
        print(f"Error logging event: {e}")


def check_initiative(template, match):
    if template.event_result.possession_kept:
        print("The initiative saved")
    else:
        match.is_home_initiative = not match.is_home_initiative
        match.save()


def fill_template_with_player(template, player):
    def get_team_name(player):
        team_player = player.team_players.first()
        return team_player.team.name if team_player else "No Team"

    player_name = f"{player.first_name} {player.last_name} ({get_team_name(player)})"

    formatted_text = template.template_text.format(player_1=player_name, player_2="")
    return formatted_text


def get_random_match_event(event_type=None):
    events_query = Event.objects.exclude(type='Team').exclude(type='Penalty').only('id', 'type')

    if event_type:
        events_query = events_query.filter(type=event_type)

    return events_query.order_by('?').first()


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


def get_event_template(event_result):
    if not event_result:
        print("No EventResult provided.")
        return None

    print(f"Searching for EventTemplates for EventResult: {event_result.event_result}")

    templates = EventTemplate.objects.filter(event_result=event_result)

    if not templates.exists():
        print(f"No EventTemplates found for EventResult: {event_result.event_result}")
        return None

    selected_template = random.choice(list(templates))
    print(f"Selected Template: {selected_template.template_text}")
    return selected_template


def get_event_result(event, success):
    if not event:
        print("No event provided.")
        return None

    print(f"Searching for EventResults for event type: {event.type} with success: {success}")

    event_results = EventResult.objects.filter(
        Q(event_type__type=event.type) & Q(event_threshold__gte=success)
    ).order_by('event_threshold')

    if not event_results.exists():
        print(f"No EventResults found for event type: {event.type}")
        return None

    print(f"Found {event_results.count()} matching EventResults.")
    selected_result = random.choice(list(event_results))
    print(f"Selected EventResult: {selected_result.event_result} with threshold {selected_result.event_threshold}")
    return selected_result


def get_event_players(template, main_player, team):
    players = [main_player]
    if template.num_players == 2:
        additional_player = (
            TeamPlayer.objects
            .filter(team=team)
            .exclude(player=main_player)  # Изключва главния играч
            .select_related('player')  # Заявява свързаните Player обекти
            .order_by('?')[:1]  # Избира случаен играч
        )
        players.extend(tp.player for tp in additional_player)  # Добавя Player обекта
    return players


def handle_card_event(event_result, player, match, team):
    current_minute = match.current_minute

    try:
        player_match_stat, created = PlayerMatchStatistic.objects.get_or_create(
            player=player,
            match=match
        )

        statistics = player_match_stat.statistics or {}

        if event_result.event_result == "RedCard":
            player.has_red_card = True
            remove_player_from_team(player, team)
            log_card_event(match, current_minute, "Red Card", player)

            statistics["RedCards"] = statistics.get("RedCards", 0) + 1

        elif event_result.event_result == "YellowCard":
            player.yellow_cards += 1
            log_card_event(match, current_minute, "Yellow Card", player)

            statistics["YellowCards"] = statistics.get("YellowCards", 0) + 1

            if player.yellow_cards >= 2:
                player.has_red_card = True
                remove_player_from_team(player, team)
                log_card_event(match, current_minute, "Red Card", player)

                statistics["RedCards"] = statistics.get("RedCards", 0) + 1

        player_match_stat.statistics = statistics
        player_match_stat.save()

        player.save()

    except Exception as e:
        print(f"Error handling card event: {e}")


def remove_player_from_team(player, team):
    try:
        team_tactics = TeamTactics.objects.select_related('team').get(team=team)
        starting_players = team_tactics.starting_players

        if starting_players.filter(pk=player.pk).exists():
            starting_players.remove(player)
            team_tactics.save()
    except TeamTactics.DoesNotExist:
        print(f"Team tactics not found for team {team.name}.")
    except Exception as e:
        print(f"Unexpected error removing player {player.first_name} {player.last_name} from team {team.name}: {e}")


def log_card_event(match, minute, card_type, player):
    if card_type not in ["Yellow Card", "Red Card"]:
        raise ValueError("Invalid card type. Must be 'Yellow Card' or 'Red Card'.")

    try:
        with transaction.atomic():
            description = f"{card_type} for {player.name} in the {minute}' minute."

            match_event_data = {
                "match": match,
                "minute": minute,
                "event_type": card_type,
                "description": description,
                "is_negative_event": True,
                "possession_kept": False,
            }

            match_event = MatchEvent.objects.create(**match_event_data)
            match_event.players.add(player)

            print(f"{card_type} logged for {player.name} in match {match.id} at minute {minute}.")
    except Exception as e:
        print(f"Error logging {card_type} for {player.name}: {e}")
