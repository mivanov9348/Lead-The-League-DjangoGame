from django.db import transaction
from match.models import MatchGoalScorer

def get_goalscorers_for_match(match):
    goal_scorers = MatchGoalScorer.objects.filter(match=match).select_related('player', 'team')

    return [
        {
            'player_name': f"{scorer.player.first_name} {scorer.player.last_name}",
            'team_name': scorer.team.name,
            'minute': scorer.minute
        }
        for scorer in goal_scorers
    ]

def log_goalscorer(match, player, team):
    try:
        with transaction.atomic():
            goalscorer = MatchGoalScorer.objects.create(
                match=match,
                player=player,
                team=team,
                minute=match.current_minute
            )
            return goalscorer
    except Exception as e:
        raise ValueError(f'Error when logging a goal: {e}')
