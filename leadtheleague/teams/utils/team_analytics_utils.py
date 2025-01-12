from collections import defaultdict
from teams.models import TeamSeasonAnalytics

TOURNAMENT_WEIGHTS = {
    'league': 1.1,
    'cup': 1,
    'euro': 1.2,
}

STATISTIC_WEIGHTS = {
    'goalscored': 0.5,       # Положителна тежест за вкараните голове
    'goalconceded': -0.5,    # Отрицателна тежест за допуснати голове
}


def get_team_analytics(limit=None, order_by=None):
    analytics = TeamSeasonAnalytics.objects.all()

    if order_by:
        analytics = analytics.order_by(*order_by)

    if limit:
        analytics = analytics[:limit]

    # Създаване на списък от речници
    analytics_data = [
        {
            'id':entry.team.id,
            'name': entry.team.name,
            'matches': entry.matches,
            'wins': entry.wins,
            'draws': entry.draws,
            'losses': entry.losses,
            'goalscored': entry.goalscored,
            'goalconceded': entry.goalconceded,
            'points': entry.points,
            'logo': entry.team.logo.url
        }
        for entry in analytics
    ]

    return analytics_data



def update_team_statistics(match, match_date):
    if not match.is_played:
        return

    weight = TOURNAMENT_WEIGHTS.get(match_date.event_type, 1)
    if weight not in TOURNAMENT_WEIGHTS.values():
        weight = 1

    try:
        home_team_stats, _ = TeamSeasonAnalytics.objects.get_or_create(
            team=match.home_team,
            season=match.season
        )
        away_team_stats, _ = TeamSeasonAnalytics.objects.get_or_create(
            team=match.away_team,
            season=match.season
        )
    except Exception as e:
        print(f"Error updating team statistics: {e}")
        return

    home_team_stats.matches += 1
    away_team_stats.matches += 1

    home_team_stats.goalscored += match.home_goals
    home_team_stats.goalconceded += match.away_goals

    away_team_stats.goalscored += match.away_goals
    away_team_stats.goalconceded += match.home_goals

    if match.home_goals > match.away_goals:
        home_team_stats.wins += 1
        away_team_stats.losses += 1
        home_team_stats.points += 3 * weight
    elif match.home_goals < match.away_goals:
        away_team_stats.wins += 1
        home_team_stats.losses += 1
        away_team_stats.points += 3 * weight
    else:
        home_team_stats.draws += 1
        away_team_stats.draws += 1
        home_team_stats.points += 1 * weight
        away_team_stats.points += 1 * weight

    home_team_stats.calculate_average()
    away_team_stats.calculate_average()

def bulk_update_team_statistics(matches, match_date):
    team_updates = defaultdict(lambda: {
        'matches': 0,
        'goalscored': 0,
        'goalconceded': 0,
        'points': 0,
        'wins': 0,
        'draws': 0,
        'losses': 0,
    })

    weight = TOURNAMENT_WEIGHTS.get(match_date.event_type, 1)

    for match in matches:
        if not match.is_played:
            continue

        # Update points, wins, draws, and losses based on match result
        if match.home_goals > match.away_goals:
            team_updates[(match.home_team.id, match.season.id)]['wins'] += 1
            team_updates[(match.away_team.id, match.season.id)]['losses'] += 1
            team_updates[(match.home_team.id, match.season.id)]['points'] += 3 * weight
        elif match.home_goals == match.away_goals:
            team_updates[(match.home_team.id, match.season.id)]['draws'] += 1
            team_updates[(match.away_team.id, match.season.id)]['draws'] += 1
            team_updates[(match.home_team.id, match.season.id)]['points'] += 1 * weight
            team_updates[(match.away_team.id, match.season.id)]['points'] += 1 * weight
        else:
            team_updates[(match.home_team.id, match.season.id)]['losses'] += 1
            team_updates[(match.away_team.id, match.season.id)]['wins'] += 1
            team_updates[(match.away_team.id, match.season.id)]['points'] += 3 * weight

        # Update matches and apply statistic weights
        team_updates[(match.home_team.id, match.season.id)]['matches'] += 1
        team_updates[(match.home_team.id, match.season.id)]['goalscored'] += match.home_goals * STATISTIC_WEIGHTS['goalscored']
        team_updates[(match.home_team.id, match.season.id)]['goalconceded'] += match.away_goals

        team_updates[(match.away_team.id, match.season.id)]['matches'] += 1
        team_updates[(match.away_team.id, match.season.id)]['goalscored'] += match.away_goals * STATISTIC_WEIGHTS['goalscored']
        team_updates[(match.away_team.id, match.season.id)]['goalconceded'] += match.home_goals

    existing_records = TeamSeasonAnalytics.objects.filter(
        team_id__in=[team_id for team_id, _ in team_updates.keys()],
        season_id__in=[season_id for _, season_id in team_updates.keys()]
    )
    records_dict = {(rec.team_id, rec.season_id): rec for rec in existing_records}

    to_create = []
    to_update = []

    for (team_id, season_id), stats in team_updates.items():
        if (team_id, season_id) in records_dict:
            record = records_dict[(team_id, season_id)]
            record.matches += stats['matches']
            record.goalscored += max(stats['goalscored'], 0)
            record.goalconceded += max(stats['goalconceded'], 0)  # Само положителни стойности
            record.points += stats['points']
            record.wins += stats['wins']
            record.draws += stats['draws']
            record.losses += stats['losses']
            to_update.append(record)
        else:
            to_create.append(TeamSeasonAnalytics(
                team_id=team_id,
                season_id=season_id,
                matches=stats['matches'],
                goalscored=max(stats['goalscored'], 0),
                goalconceded=max(stats['goalconceded'], 0),
                points=stats['points'],
                wins=stats['wins'],
                draws=stats['draws'],
                losses=stats['losses'],
            ))

    if to_create:
        TeamSeasonAnalytics.objects.bulk_create(to_create)
    if to_update:
        TeamSeasonAnalytics.objects.bulk_update(
            to_update,
            ['matches', 'goalscored', 'goalconceded', 'points', 'wins', 'draws', 'losses']
        )

