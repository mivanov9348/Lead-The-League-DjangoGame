from django.db import transaction
from django.db.models import F, Q, Sum, Value as V, Case, When, FloatField
from match.models import MatchEvent, Event
from players.models import Player
from teams.models import TeamTactics, TeamPlayer


def check_rotation_violations(team, taken_penalty_players):
    unique_players = set(taken_penalty_players)
    total_players = TeamPlayer.objects.filter(team=team).count()

    print(f"Taken penalty players: {unique_players}")
    print(f"Total players in team: {total_players}")

    return len(unique_players) == total_players


def update_penalty_initiative(match_penalties):
    if not match_penalties.current_initiative:
        raise ValueError("Current initiative is not set.")

    print(f"Before Update: {match_penalties.current_initiative.name}")
    match_penalties.current_initiative = (
        match_penalties.match.away_team if match_penalties.current_initiative == match_penalties.match.home_team
        else match_penalties.match.home_team
    )
    match_penalties.save()
    print(f"After Update: {match_penalties.current_initiative.name}")


def get_penalty_taker(team, taken_penalty_players):
    team_tactics = TeamTactics.objects.select_related('team').get(team=team)

    available_players = team_tactics.starting_players.exclude(id__in=taken_penalty_players)

    # Annotate scores for each attribute separately
    sorted_players = available_players.annotate(
        shooting_score=Case(
            When(playerattribute__attribute__name="Shooting", then=F('playerattribute__value') * 0.5),
            default=V(0),
            output_field=FloatField()
        ),
        finishing_score=Case(
            When(playerattribute__attribute__name="Finishing", then=F('playerattribute__value') * 0.3),
            default=V(0),
            output_field=FloatField()
        ),
        determination_score=Case(
            When(playerattribute__attribute__name="Determination", then=F('playerattribute__value') * 0.2),
            default=V(0),
            output_field=FloatField()
        )
    ).annotate(
        total_score=F('shooting_score') + F('finishing_score') + F('determination_score')
    ).order_by('-total_score')

    return sorted_players.first()


def get_penalty_match_event():
    event = Event.objects.filter(type='Penalty').first()

    if event:
        print(f"Random event generated: {event.type} with success rate {event.success_rate}")
    else:
        print(f"No event found.")
    return event


def update_penalty_score(match_penalties, is_goal, team):
    if is_goal:
        if team == match_penalties.match.home_team:
            match_penalties.home_score += 1
        elif team == match_penalties.match.away_team:
            match_penalties.away_score += 1
    match_penalties.save()


def calculate_penalty_success(event_result):
    if event_result == "PenaltyMiss":
        print("Miss")
        return False
    elif event_result == "PenaltyGoal":
        print("Goal")
        return True
    else:
        print("Invalid event result")
        return "Invalid event result"

def check_penalties_completion(match_penalties):
    home_attempts = match_penalties.attempts.filter(team=match_penalties.match.home_team).count()
    away_attempts = match_penalties.attempts.filter(team=match_penalties.match.away_team).count()

    home_score = match_penalties.attempts.filter(team=match_penalties.match.home_team, is_goal=True).count()
    away_score = match_penalties.attempts.filter(team=match_penalties.match.away_team, is_goal=True).count()

    remaining_home_attempts = 5 - home_attempts
    remaining_away_attempts = 5 - away_attempts

    if home_score > away_score + remaining_away_attempts:
        match_penalties.is_completed = True
        match_penalties.save()
        return True

    if away_score > home_score + remaining_home_attempts:
        match_penalties.is_completed = True
        match_penalties.save()
        return True

    if home_attempts == 5 and away_attempts == 5:
        if home_score != away_score:
            match_penalties.is_completed = True
            match_penalties.save()
            return True

    return False

def check_sudden_death_completion(match_penalties):
    home_attempts = match_penalties.attempts.filter(team=match_penalties.match.home_team).count()
    away_attempts = match_penalties.attempts.filter(team=match_penalties.match.away_team).count()

    if home_attempts > 5 and away_attempts > 5 and abs(home_attempts - away_attempts) <= 1:
        home_score = match_penalties.attempts.filter(team=match_penalties.match.home_team, is_goal=True).count()
        away_score = match_penalties.attempts.filter(team=match_penalties.match.away_team, is_goal=True).count()

        if abs(home_score - away_score) == 1:  # One team leads by one goal
            match_penalties.is_completed = True
            match_penalties.save()
            return True

    return False


def log_penalty_event(match, formatted_template, penalty_taker, is_goal):
    if not isinstance(penalty_taker, Player):
        raise ValueError("penalty_taker трябва да бъде обект от типа 'Player'.")

    try:
        with transaction.atomic():
            event_type = "PenaltyGoal" if is_goal else "PenaltyMiss"

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
