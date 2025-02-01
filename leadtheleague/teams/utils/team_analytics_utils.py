import os
from collections import defaultdict
import pandas as pd
from django.db import transaction
from matplotlib import pyplot as plt
from django.conf import settings

from teams.models import TeamSeasonAnalytics, Team

TOURNAMENT_WEIGHTS = {
    'league': 1.1,
    'cup': 1,
    'euro': 1.2,
}

STATISTIC_WEIGHTS = {
    'goalscored': 0.5,  # Положителна тежест за вкараните голове
    'goalconceded': -0.5,  # Отрицателна тежест за допуснати голове
}


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
        team_updates[(match.home_team.id, match.season.id)]['goalscored'] += match.home_goals * STATISTIC_WEIGHTS[
            'goalscored']
        team_updates[(match.home_team.id, match.season.id)]['goalconceded'] += match.away_goals
        team_updates[(match.away_team.id, match.season.id)]['matches'] += 1
        team_updates[(match.away_team.id, match.season.id)]['goalscored'] += match.away_goals * STATISTIC_WEIGHTS[
            'goalscored']
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


def get_league_season_statistics(season):
    analytics = TeamSeasonAnalytics.objects.filter(season=season).values(
        'team__name',
        'matches',
        'wins',
        'draws',
        'losses',
        'goalscored',
        'goalconceded',
        'points'
    )
    print("Analytics data:", analytics)

    return list(analytics)

def process_league_season_data(season):
    raw_data = get_league_season_statistics(season)
    print("Raw data:", raw_data)

    if not raw_data:
        print("No data returned!")
        return None

    df = pd.DataFrame(raw_data)
    print("DataFrame columns:", df.columns)

    df['goal_difference'] = df['goalscored'] - df['goalconceded']
    df = df.sort_values(by='points', ascending=False)

    print("Sorted DataFrame:", df)
    return df

def plot_team_points(df):
    # Създаваме стълбовидна графика
    plt.figure(figsize=(10, 6))
    plt.bar(df['team__name'], df['points'], color='skyblue')

    # Настройки на графиката
    plt.title('Точки на отборите за сезона', fontsize=16)
    plt.xlabel('Отбори', fontsize=12)
    plt.ylabel('Точки', fontsize=12)
    plt.xticks(rotation=45, ha='right')  # Завъртане на имената за по-добра четимост

    # Показване на графиката
    plt.tight_layout()
    plt.show()

def plot_goals_scored(df):
    # Създаваме линейна графика
    plt.figure(figsize=(10, 6))
    plt.plot(df['team__name'], df['goalscored'], marker='o', linestyle='-', color='green', label='Отбелязани голове')

    # Настройки на графиката
    plt.title('Отбелязани голове на отборите', fontsize=16)
    plt.xlabel('Отбори', fontsize=12)
    plt.ylabel('Голове', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    # Показване на легенда и графиката
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_points_vs_goal_difference(df):
    # Добавяме разлика в головете, ако още я няма
    if 'goal_difference' not in df.columns:
        df['goal_difference'] = df['goalscored'] - df['goalconceded']

    # Създаваме разпръсната графика
    plt.figure(figsize=(10, 6))
    plt.scatter(df['goal_difference'], df['points'], color='purple', s=100, alpha=0.7)

    # Настройки на графиката
    plt.title('Точки спрямо разлика в головете', fontsize=16)
    plt.xlabel('Разлика в головете', fontsize=12)
    plt.ylabel('Точки', fontsize=12)

    # Показване на графиката
    plt.tight_layout()
    plt.show()

def save_plot_to_file(df, plot_function, file_name):
    plot_function(df)

    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    plt.savefig(file_path, format='png')
    plt.close()
    return file_path