from django.db import transaction
from game.models import Settings
from players.models import Player
from players.utils.generate_player_utils import generate_player_season_stats
from teams.models import TeamSeasonStats, Team

def update_team_stats(match):
    if not match.is_played:
        print('Match is still unplayed!')
        return

    home_team = match.home_team
    away_team = match.away_team
    home_goals = match.home_goals
    away_goals = match.away_goals

    home_stats, _ = TeamSeasonStats.objects.get_or_create(
        team=home_team,
        season=match.season,
        league=match.league
    )
    away_stats, _ = TeamSeasonStats.objects.get_or_create(
        team=away_team,
        season=match.season,
        league=match.league
    )

    draw_points = Settings.objects.get(name='League_Draw_Points').value
    win_points = Settings.objects.get(name='League_Win_Points').value

    with transaction.atomic():
        home_stats.matches += 1
        away_stats.matches += 1

        if home_goals > away_goals:
            home_stats.wins += 1
            home_stats.points += win_points
            away_stats.losses += 1

        elif home_goals < away_goals:
            away_stats.wins += 1
            away_stats.points += win_points
            home_stats.losses += 1

        else:
            home_stats.draws += 1
            away_stats.draws += 1
            home_stats.points += draw_points
            away_stats.points += draw_points

        home_stats.goalscored += home_goals
        home_stats.goalconceded += away_goals
        away_stats.goalscored += away_goals
        away_stats.goalconceded += home_goals

        home_stats.goaldifference = home_stats.goalscored - home_stats.goalconceded
        away_stats.goaldifference = away_stats.goalscored - away_stats.goalconceded

        home_stats.save()
        away_stats.save()

def boost_reputation(team, reputation_increase):
    new_reputation = team.reputation + reputation_increase
    team.reputation = max(1000, min(new_reputation, 10000)) #за settings
    team.save()

def reduce_reputation(team, reputation_decrease):
    new_reputation = team.reputation + reputation_decrease
    team.popularity = max(1000, min(new_reputation, 10000))  # за settings
    team.save()

def create_team_season_stats(new_season):
    with transaction.atomic():
        teams = Team.objects.all()
        for team in teams:
            if not TeamSeasonStats.objects.filter(team=team, season=new_season).exists():
                league = team.league

                TeamSeasonStats.objects.create(
                    team=team,
                    season=new_season,
                    league=league
                )

            players = Player.objects.filter(team_players__team=team)
            for player in players:
                generate_player_season_stats(player, new_season, team)