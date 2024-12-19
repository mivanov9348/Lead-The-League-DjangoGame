from django.db import transaction
from django.utils import timezone
from cups.models import SeasonCup
from fixtures.models import LeagueFixture, EuropeanCupFixture, CupFixture
from game.models import Season
from game.utils.get_season_stats_utils import get_current_season
from match.models import Match
from players.models import Player, PlayerMatchStatistic
from django.db import transaction

def generate_matches_from_fixtures(fixtures, event_type, season):
    matches_to_create = []

    for fixture in fixtures:
        match_data = {
            'home_team': fixture.home_team,
            'away_team': fixture.away_team,
            'match_date': fixture.date,
            'match_time': fixture.match_time,
            'home_goals': fixture.home_goals,
            'away_goals': fixture.away_goals,
            'is_played': fixture.is_finished,
            'season': season,
        }

        if event_type == 'league':
            match_data['league'] = fixture.league
            match_data['season_cup'] = None
        elif event_type == 'cup':
            match_data['season_cup'] = fixture.season_cup
            match_data['league'] = None
        elif event_type == 'euro_cup':
            match_data['league'] = None
            match_data['season_cup'] = None

        matches_to_create.append(Match(**match_data))

    with transaction.atomic():
        Match.objects.bulk_create(matches_to_create)

    print(f"Създадени са {len(matches_to_create)} мачове за {event_type} сезона {season.year}.")


def generate_league_matches(season=None):
    if season is None:
        season = get_current_season()

    league_fixtures = LeagueFixture.objects.filter(season=season)
    generate_matches_from_fixtures(league_fixtures, event_type='league', season=season)


def generate_cup_matches(season=None):
    if season is None:
        season = get_current_season()

    cup_fixtures = CupFixture.objects.filter(season=season)
    generate_matches_from_fixtures(cup_fixtures, event_type='cup', season=season)


def generate_euro_cup_matches(season=None):
    if season is None:
        season = get_current_season()

    euro_cup_fixtures = EuropeanCupFixture.objects.filter(season=season)
    generate_matches_from_fixtures(euro_cup_fixtures, event_type='euro_cup', season=season)


def generate_player_day_match_stats(players, today=None):
    today = today or timezone.now().date()
    current_season = get_current_season()

    if not current_season:
        return "No active season found."

    matches = Match.objects.filter(season=current_season, match_date=today)
    if not matches.exists():
        return f"No matches found for {today}."

    players_to_process = list(players)  # Уверяваме се, че играчите са списък

    with transaction.atomic():
        stats_created = 0  # Брояч за създадените статистики

        for player in players_to_process:
            player_teams = player.team_players.values_list('teams', flat=True)
            player_matches = matches.filter(
                home_team_id__in=player_teams
            ) | matches.filter(
                away_team_id__in=player_teams
            )

            for match in player_matches:
                # Проверяваме дали вече има статистика за този играч в конкретния мач
                if not PlayerMatchStatistic.objects.filter(player=player, match=match).exists():
                    PlayerMatchStatistic.objects.create(
                        player=player,
                        match=match,
                        statistics={
                            "Goals": 0,
                            "Assists": 0,
                            "Passes": 0,
                            "Shoots": 0,
                            "ShootsOnTarget": 0,
                            "Tackles": 0,
                            "YellowCards": 0,
                            "RedCards": 0,
                            "Saves": 0,
                        }
                    )
                    stats_created += 1

    return f"Successfully generated {stats_created} player match statistics."

def generate_all_player_day_match_stats():
    today = timezone.now().date()
    current_season = Season.objects.filter(is_ended=False).first()
    if not current_season:
        return

    matches = Match.objects.filter(season=current_season, match_date=today)

    players = Player.objects.prefetch_related('team_players').filter(is_free_agent=False)

    with transaction.atomic():
        for match in matches:
            for player in players:
                teams = player.team_players.values_list('teams', flat=True)
                if match.home_team_id in teams or match.away_team_id in teams:
                    if not PlayerMatchStatistic.objects.filter(player=player, match=match).exists():
                        PlayerMatchStatistic.objects.create(
                            player=player,
                            match=match,
                            statistics={
                                "Goals": 0,
                                "Assists": 0,
                                "Passes": 0,
                                "Shoots": 0,
                                "ShootsOnTarget": 0,
                                "Tackles": 0,
                                "YellowCards": 0,
                                "RedCards": 0,
                                "Saves": 0,
                            }
                        )
