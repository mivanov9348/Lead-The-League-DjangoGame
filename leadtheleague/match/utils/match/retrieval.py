import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone

from europeancups.models import KnockoutStage
from match.models import Match
from teams.models import Team


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


def get_opposing_team(match, team):
    if team == match.home_team:
        return match.away_team
    elif team == match.away_team:
        return match.home_team
    else:
        raise ValueError(f"Team {team} is not part of this match.")
