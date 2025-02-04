import os

from django.db import transaction

from leadtheleague import settings
from teams.models import Team


def update_team_stats(match):
    if not match.is_played:
        print('Match is still unplayed!')
        return

    # home_team = match.home_team
    # away_team = match.away_team
    # home_goals = match.home_goals
    # away_goals = match.away_goals
    #
    # home_stats, _ = TeamSeasonStats.objects.get_or_create(
    #     teams=home_team,
    #     season=match.season,
    #     league=match.league
    # )
    # away_stats, _ = TeamSeasonStats.objects.get_or_create(
    #     teams=away_team,
    #     season=match.season,
    #     league=match.league
    # )
    #
    # draw_points = Settings.objects.get(name='League_Draw_Points').value
    # win_points = Settings.objects.get(name='League_Win_Points').value
    #
    # with transaction.atomic():
    #     home_stats.matches += 1
    #     away_stats.matches += 1
    #
    #     if home_goals > away_goals:
    #         home_stats.wins += 1
    #         home_stats.points += win_points
    #         away_stats.losses += 1
    #
    #     elif home_goals < away_goals:
    #         away_stats.wins += 1
    #         away_stats.points += win_points
    #         home_stats.losses += 1
    #
    #     else:
    #         home_stats.draws += 1
    #         away_stats.draws += 1
    #         home_stats.points += draw_points
    #         away_stats.points += draw_points
    #
    #     home_stats.goalscored += home_goals
    #     home_stats.goalconceded += away_goals
    #     away_stats.goalscored += away_goals
    #     away_stats.goalconceded += home_goals
    #
    #     home_stats.goaldifference = home_stats.goalscored - home_stats.goalconceded
    #     away_stats.goaldifference = away_stats.goalscored - away_stats.goalconceded
    #
    #     home_stats.save()
    #     away_stats.save()


def boost_reputation(team, reputation_increase):
    new_reputation = team.reputation + reputation_increase
    team.reputation = max(1000, min(new_reputation, 10000))  # за settings
    team.save()


def reduce_reputation(team, reputation_decrease):
    new_reputation = team.reputation + reputation_decrease
    team.popularity = max(1000, min(new_reputation, 10000))  # за settings
    team.save()


def set_team_logos():
    all_teams = Team.objects.all()
    logos_dir = os.path.join(settings.MEDIA_ROOT, 'logos')  # Коригирано към MEDIA_ROOT
    successful_teams = 0
    errors = []

    for team in all_teams:
        logo_filename = f"{team.name}.png"
        logo_path = os.path.join(logos_dir, logo_filename)

        if os.path.exists(logo_path):
            try:
                with transaction.atomic():  # Използване на транзакция за надеждност
                    team.logo = f"logos/{logo_filename}"
                    team.save(update_fields=['logo'])
                    successful_teams += 1
            except Exception as e:
                errors.append(f"Error setting logo for team {team.name}: {e}")
        else:
            errors.append(f"Logo not found for team {team.name}")

    return successful_teams, errors