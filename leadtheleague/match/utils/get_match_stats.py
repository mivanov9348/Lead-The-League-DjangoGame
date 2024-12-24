from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import random
from django.db.models import Q
from match.models import Match, Event, AttributeEventWeight, EventResult, EventTemplate
from teams.models import Team
from teams.utils.team_finance_utils import team_match_profit

def get_match_by_id(match_id):
    return Match.objects.filter(id=match_id).only('id', 'home_team', 'away_team', 'match_date').first()

def get_match_by_fixture(fixture):
    try:
        content_type = ContentType.objects.get_for_model(fixture)
        match = Match.objects.get(fixture_content_type=content_type, fixture_object_id=fixture.id)
        return match
    except Match.DoesNotExist:
        raise ValueError(f"No match found for fixture: {fixture}")

def get_matches_by_stadium(stadium, start_date=None, end_date=None):
    matches = Match.objects.filter(stadium=stadium)

    if start_date and end_date:
        matches = matches.filter(match_date__range=(start_date, end_date))
    elif start_date:
        matches = matches.filter(match_date__gte=start_date)
    elif end_date:
        matches = matches.filter(match_date__lte=end_date)

    return matches


def get_user_today_match(user):
    today = timezone.now().date()
    user_team = Team.objects.only('id').get(user=user)

    next_match = Match.objects.filter(
        Q(home_team=user_team) | Q(away_team=user_team),
        match_date__gte=today
    ).select_related('home_team', 'away_team').only('home_team', 'away_team', 'match_date', 'match_time').first()

    return next_match


def get_match_status(match):
    current_time = timezone.now()
    match_datetime = timezone.make_aware(datetime.combine(match.match_date, match.match_time))

    if match.is_played:
        return 'Ended'
    elif current_time < match_datetime:
        return 'Upcoming'
    else:
        return 'LIVE'


def get_random_match_event():
    event = Event.objects.exclude(type='Team').only('id', 'type')
    return random.choice(list(event))


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
            return EventTemplate.objects.filter(event_result=event_result).select_related('event_result').only(
                'id').first()
    return None


def get_event_players(template, main_player, team):
    players = [main_player]
    if template.num_players == 2:
        players.extend(
            player for player in Team.objects.exclude(id=main_player.id)
                                 .only('id').order_by('?')[:1]
        )
    return players


def calculate_match_attendance(match):
    max_capacity = match.stadium.capacity
    base_popularity = match.home_team.reputation + (match.away_team.reputation // 2)
    stadium_boost = match.stadium.tier.popularity_bonus

    raw_attendance = (base_popularity + stadium_boost) * random.uniform(1.8, 2.2)
    attendance = min(int(raw_attendance), max_capacity)
    return attendance


def match_income(match, team):
    ticket_price = match.stadium.ticket_price
    attendance = calculate_match_attendance(match)
    income = attendance * ticket_price
    team_match_profit(team, income, f'{match.home_team} - {match.away_team} (attendance: {attendance})')
