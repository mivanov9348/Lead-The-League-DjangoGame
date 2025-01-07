import random
from django.db import transaction
from match.models import MatchEvent, Event, AttributeEventWeight, EventResult, EventTemplate
from match.utils.get_match_stats import calculate_match_attendance, match_income
from match.utils.match_goalscorers_utils import log_goalscorer
from players.models import PlayerMatchStatistic
from players.utils.get_player_stats_utils import get_player_attributes
from teams.models import TeamTactics, TeamPlayer


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

        if hasattr(match, 'penalties') and match.penalties.is_completed:
            penalties = match.penalties
            print(f"Match went to penalties: Home {penalties.home_score} - Away {penalties.away_score}")

            if penalties.home_score > penalties.away_score:
                match.winner = match.home_team
            elif penalties.away_score > penalties.home_score:
                match.winner = match.away_team
            else:
                raise ValueError("Invalid state: Penalties completed but no winner determined.")
        else:
            if match.home_goals > match.away_goals:
                match.winner = match.home_team
            elif match.away_goals > match.home_goals:
                match.winner = match.away_team
            else:
                match.winner = None  # Равен резултат

        calculate_match_attendance(match)
        match_income(match, match.home_team)
        match.save()

        fixture = match.fixture
        if not fixture:
            raise ValueError("Мачът няма свързан fixture.")

        fixture.home_goals = match.home_goals
        fixture.away_goals = match.away_goals
        fixture.is_finished = True

        fixture.winner = match.winner
        fixture.save()

    print(f"Match finalized: {match}. Fixture updated.")


def update_player_stats_from_template(match, event_result, player):
    if not player:
        print("No player provided for statistics update.")

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
            stat_value = getattr(event_result, field, 0)
            if stat_value > 0:
                updated_stats[stat_name] = updated_stats.get(stat_name, 0) + stat_value

        player_stat.statistics = updated_stats
        player_stat.save()


def update_match_score(event_result, match, team_with_initiative, player):
    goal_events = {"ShotGoal", "CornerGoal", "FreeKickGoal", "PenaltyGoal"}

    if event_result.event_result in goal_events:
        log_goalscorer(match, player, team_with_initiative)
        if team_with_initiative == match.home_team:
            match.home_goals += 1
        else:
            match.away_goals += 1

        match.save()


def log_match_event(match, minute, template, formatted_text, player=None):
    if not player:
        raise ValueError("No player provided!")

    try:
        with transaction.atomic():
            match_event = MatchEvent.objects.create(
                match=match,
                minute=minute,
                event_type=template.event_result,
                description=formatted_text,
                is_negative_event=template.event_result.is_negative_event,
                possession_kept=template.event_result.possession_kept
            )

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

    formatted_text = template.template_text.format(player_1=player_name)
    return formatted_text


def get_random_match_event():
    events_query = Event.objects.exclude(type__in=['Team', 'Penalty']).only('id', 'type', 'success_rate')

    event = events_query.order_by('?').first()

    if event:
        print(f"Random event generated: {event.type} with success rate {event.success_rate}")
    else:
        print("No events found matching the criteria.")

    return event


def get_event_weights(event):
    weights = AttributeEventWeight.objects.filter(event=event).select_related('attribute')
    if not weights.exists():
        print(f"No AttributeEventWeight entries found for event {event}.")
        return {}

    return {
        weight.attribute.name: weight.weight for weight in weights
    }


def calculate_event_success_rate(event, player):
    # Get player attributes and event weights
    player_attributes = get_player_attributes(player)
    event_weights = get_event_weights(event)
    print(f'eventweig : {event_weights}')

    # Calculate the weighted sum
    attributes_and_weights = [
        (player_attributes.get(attr_name, 0), weight)
        for attr_name, weight in event_weights.items()
    ]

    weighted_sum = sum(attribute_value * weight for attribute_value, weight in attributes_and_weights)
    print(f'weighted sum: {weighted_sum}')

    luck_factor = random.uniform(-3.0, 3.0)
    print(f"Luck factor: {luck_factor}")

    final_success_rate = round(event.success_rate + weighted_sum + luck_factor, 2)
    final_success_rate = min(100.0, final_success_rate)
    print(f"Final success rate: {final_success_rate}")

    return final_success_rate


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
        event_type__type=event.type
    ).order_by('-event_threshold')

    if not event_results.exists():
        print(f"No EventResults found for event type: {event.type}")
        return None

    print(f"Found {event_results.count()} matching EventResults.")

    last_valid_result = None

    for event_result in event_results:
        print(f"Checking if success {success} <= threshold {event_result.event_threshold}")
        if success <= event_result.event_threshold:
            last_valid_result = event_result
            print(f"Selected EventResult: {event_result.event_result} with threshold {event_result.event_threshold}")

    if last_valid_result:
        return last_valid_result

    print("No valid EventResult found.")
    return None


def get_event_players(template, main_player, team):
    players = [main_player]
    if template.num_players == 2:
        additional_player = (
            TeamPlayer.objects
            .filter(team=team)
            .exclude(player=main_player)
            .select_related('player')
            .order_by('?')[:1]
        )
        players.extend(tp.player for tp in additional_player)
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
