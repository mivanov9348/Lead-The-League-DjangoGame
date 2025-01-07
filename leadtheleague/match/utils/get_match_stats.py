from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import random
from django.db.models import Q
from match.models import Match
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

    next_unplayed_match = Match.objects.filter(
        (Q(home_team=user_team) | Q(away_team=user_team)),
        match_date__gte=today,
        is_played=False
    ).select_related('home_team', 'away_team').only(
        'home_team', 'away_team', 'match_date', 'match_time', 'is_played'
    ).order_by('match_date', 'match_time').first()  # Уверяваме се, че сортираме по дата и време

    return next_unplayed_match


def get_user_last_match(user):
    user_team = Team.objects.only('id').get(user=user)

    last_played_match = Match.objects.filter(
        (Q(home_team=user_team) | Q(away_team=user_team)),
        is_played=True
    ).select_related('home_team', 'away_team').only(
        'home_team', 'away_team', 'match_date', 'match_time', 'is_played', 'home_goals', 'away_goals'
    ).order_by('-match_date', '-match_time').first()

    return last_played_match


def get_match_status(match):
    current_time = timezone.now()
    match_datetime = timezone.make_aware(datetime.combine(match.match_date, match.match_time))

    if match.is_played:
        return 'Ended'
    elif current_time < match_datetime:
        return 'Upcoming'
    else:
        return 'LIVE'


def calculate_match_attendance(match):
    max_capacity = 1000
    if match.stadium and match.stadium.capacity:
        max_capacity = match.stadium.capacity

    base_popularity = match.home_team.reputation + (match.away_team.reputation // 2)
    stadium_boost = match.stadium.tier.popularity_bonus if match.stadium and match.stadium.tier else 0

    raw_attendance = (base_popularity + stadium_boost) * random.uniform(1.8, 2.2)
    attendance = min(int(raw_attendance), max_capacity)
    match.attendance = attendance
    match.save()
    return attendance


def match_income(match, team):
    ticket_price = 10
    if match.stadium and match.stadium.ticket_price:
        ticket_price = match.stadium.ticket_price

    attendance = calculate_match_attendance(match)
    income = attendance * ticket_price
    team_match_profit(team, match, income, f'{match.home_team} - {match.away_team} (attendance: {attendance})')
