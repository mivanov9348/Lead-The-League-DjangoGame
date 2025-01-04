from django.db import transaction
from django.db.models import F

from match.models import MatchEvent
from players.models import Player
from teams.models import TeamTactics

def check_rotation_violations(team, taken_penalty_players):
    player_ids = [attempt.player_id for attempt in taken_penalty_players]
    unique_players = set(player_ids)

    if len(unique_players) == team.player_set.count():
        return True
    return False

def update_penalty_initiative(match_penalties):
    match_penalties.current_initiative = (
        match_penalties.match.away_team if match_penalties.current_initiative == match_penalties.match.home_team
        else match_penalties.match.home_team
    )
    match_penalties.save()

def get_penalty_taker(team, taken_penalty_players):
    team_tactics = TeamTactics.objects.select_related('team').get(team=team)

    sorted_players = team_tactics.starting_players.exclude(id__in=taken_penalty_players).annotate(
        total_score=F('shooting') * 0.5 + F('finishing') * 0.3 + F('determination') * 0.2
    ).order_by('-total_score')

    return sorted_players.first()

def update_penalty_score(match_penalties, is_goal, team):
    if is_goal:
        if team == match_penalties.match.home_team:
            match_penalties.home_score += 1
        elif team == match_penalties.match.away_team:
            match_penalties.away_score += 1
    match_penalties.save()

def check_penalties_completion(match_penalties):
    home_attempts = match_penalties.attempts.filter(team=match_penalties.match.home_team).count()
    away_attempts = match_penalties.attempts.filter(team=match_penalties.match.away_team).count()

    if home_attempts >= 5 or away_attempts >= 5:
        max_possible_home_score = match_penalties.home_score + (5 - home_attempts)
        max_possible_away_score = match_penalties.away_score + (5 - away_attempts)

        if match_penalties.home_score > max_possible_away_score or match_penalties.away_score > max_possible_home_score:
            match_penalties.is_completed = True
            match_penalties.save()
            return True

    if home_attempts > 5 and away_attempts > 5 and abs(home_attempts - away_attempts) <= 1:
        if match_penalties.home_score != match_penalties.away_score:
            match_penalties.is_completed = True
            match_penalties.save()
            return True

    return False


def log_penalty_event(match, formatted_template, penalty_taker, is_goal):
    if not isinstance(penalty_taker, Player):
        raise ValueError("penalty_taker трябва да бъде обект от типа 'Player'.")

    try:
        with transaction.atomic():
            event_type = "Penalty Goal" if is_goal else "Penalty Miss"

            match_event_data = {
                "match": match,
                "minute": 90,
                "event_type": "Penalty",
                "description": formatted_template,
                "is_negative_event": not is_goal,
                "possession_kept": False,
            }

            match_event = MatchEvent.objects.create(**match_event_data)

            match_event.players.set([penalty_taker])

            print(f"Успешно логирано събитие: {formatted_template}")
    except Exception as e:
        print(f"Грешка при логване на събитие за дузпа: {e}")