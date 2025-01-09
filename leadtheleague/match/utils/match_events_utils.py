from django.db import transaction

from match.models import MatchEvent, EventResult, EventTemplate, Event
import random

from players.utils.get_player_stats_utils import get_player_attributes
from teams.models import TeamPlayer


def create_match_event(match, event_result_name, players=None, is_negative_event=False, possession_kept=True):
    try:
        event_result = EventResult.objects.get(event_result=event_result_name)

        event_templates = EventTemplate.objects.filter(event_result=event_result)

        if not event_templates.exists():
            raise ValueError(f"No templates found for EventResult '{event_result_name}'.")

        event_template = random.choice(event_templates)
        description = event_template.template_text

        event = create_match_event_instance(
            match=match,
            minute=match.current_minute,
            event_type=event_result_name,
            description=description,
            is_negative_event=is_negative_event,
            possession_kept=possession_kept
        )

        if players:
            event.players.set(players)
        event.save()

        return event

    except EventResult.DoesNotExist:
        raise ValueError(f"EventResult with name '{event_result_name}' does not exist.")
    except Exception as e:
        raise ValueError(f"Error creating MatchEvent: {str(e)}")

def create_match_event_instance(match, minute, event_type, description, is_negative_event, possession_kept):
    return MatchEvent.objects.create(
        match=match,
        minute=minute,
        event_type=event_type,
        description=description,
        is_negative_event=is_negative_event,
        possession_kept=possession_kept
    )

def create_kickoff_match_event(match, players=None, is_negative_event=False, possession_kept=True):
    return create_match_event(match, 'KickOff', players, is_negative_event, possession_kept)

def create_match_end_match_event(match, players=None, is_negative_event=False, possession_kept=True):
    return create_match_event(match, 'FullTime', players, is_negative_event, possession_kept)

def create_penalty_start_match_event(match, players=None, is_negative_event=False, possession_kept=True):
    return create_match_event(match, 'PenaltyStart', players, is_negative_event, possession_kept)


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
    attributes_dict = {attr['name']: attr['value'] for attr in player_attributes}
    attributes_and_weights = [
        (attributes_dict.get(attr_name, 0), weight)
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