import datetime
from random import random
from django.db.models import Q
from django.utils import timezone

from match.models import Match, Event, AttributeEventWeight, EventResult, EventTemplate
from match.utils.processing_match_utils import choose_event_random_player
from teams.models import Team

def get_user_today_match(user):
    today = timezone.now().date()
    user_team = Team.objects.get(user=user)

    next_match = Match.objects.filter(
        Q(home_team=user_team) | Q(away_team=user_team),
        match_date__gte=today
    ).select_related('home_team', 'away_team').first()

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

def get_random_match_event():
    event = Event.objects.exclude(type='Team')
    return random.choice(event)

def get_match_event_attributes_weight(event, player_attributes):
    weights = AttributeEventWeight.objects.filter(event=event)
    attributes_and_weights = []

    for weight in weights:
        attribute_value = player_attributes.get(weight.attribute)
        if attribute_value is not None:
            attributes_and_weights.append((attribute_value, weight.weight))
    return attributes_and_weights

def get_event_success_rate(event, attributes_and_weights):
    base_success = event.success_rate

    for attribute_value, weight in attributes_and_weights:
        base_success += (attribute_value * weight)

    return round(base_success, 2)

def get_match_event_template(event_type, success):
    event_results = EventResult.objects.filter(event_type__type=event_type).order_by('event_threshold')
    chosen_template = None

    for event_result in event_results:
        if success <= event_result.event_threshold:
            chosen_template = EventTemplate.objects.filter(event_result=event_result).select_related(
                'event_result').first()
            break

    return chosen_template

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

def get_team_players(team):
    return team.players.all()