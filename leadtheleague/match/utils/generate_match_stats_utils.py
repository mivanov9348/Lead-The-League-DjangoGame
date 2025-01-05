from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from fixtures.models import LeagueFixture, EuropeanCupFixture, CupFixture
from game.models import Season
from game.utils.get_season_stats_utils import get_current_season
from match.models import Match, MatchPenalties
from players.models import Player, PlayerMatchStatistic, Statistic
from django.db import transaction
from teams.models import TeamTactics


def generate_matches_from_fixtures(fixtures, event_type, season):
    matches_to_create = []
    print(f"Generating matches for {event_type} - season {season.year}.")

    for fixture in fixtures:
        print(f"Processing Fixture ID {fixture.id}: {fixture.home_team} vs {fixture.away_team}")

        if event_type == 'euro_cup' and not fixture.european_cup_season:
            print(f"Skipping Fixture ID {fixture.id} - Missing European Cup season.")
            continue

        content_type = ContentType.objects.get_for_model(fixture)
        if Match.objects.filter(fixture_content_type=content_type, fixture_object_id=fixture.id).exists():
            print(f"Skipping Fixture ID {fixture.id} - Match already exists.")
            continue

        # Prepare match data
        match_data = {
            'home_team': fixture.home_team,
            'away_team': fixture.away_team,
            'match_date': fixture.date,
            'match_time': fixture.match_time,
            'home_goals': fixture.home_goals,
            'away_goals': fixture.away_goals,
            'is_played': fixture.is_finished,
            'stadium': getattr(fixture.home_team, 'stadium', None),
            'season': season,
            'fixture_content_type': content_type,
            'fixture_object_id': fixture.id,
        }

        if event_type == 'league':
            match_data['league_season'] = fixture.league_season
        elif event_type == 'cup':
            match_data['season_cup'] = fixture.season_cup
        elif event_type == 'euro_cup':
            match_data['european_cup_season'] = fixture.european_cup_season

        matches_to_create.append(Match(**match_data))

    if not matches_to_create:
        print("No matches to create.")
        return

    # Bulk create matches
    with transaction.atomic():
        Match.objects.bulk_create(matches_to_create)

    print(f"Successfully created {len(matches_to_create)} matches.")


def generate_league_matches(season=None):
    if season is None:
        season = get_current_season()

    league_fixtures = LeagueFixture.objects.filter(league_season__season=season)
    generate_matches_from_fixtures(league_fixtures, event_type='league', season=season)


def generate_cup_matches(season=None):
    if season is None:
        season = get_current_season()

    cup_fixtures = CupFixture.objects.filter(season_cup__season=season)
    generate_matches_from_fixtures(cup_fixtures, event_type='cup', season=season)


def generate_euro_cup_matches(season=None):
    if season is None:
        season = get_current_season()

    euro_cup_fixtures = EuropeanCupFixture.objects.filter(european_cup_season__season=season)
    generate_matches_from_fixtures(euro_cup_fixtures, event_type='euro_cup', season=season)


def generate_players_match_stats(match):
    home_tactics = TeamTactics.objects.filter(team=match.home_team).first()
    away_tactics = TeamTactics.objects.filter(team=match.away_team).first()

    if not home_tactics or not away_tactics:
        raise ValueError("Team tactics not found for one of the teams.")

    starting_players = list(home_tactics.starting_players.all()) + list(away_tactics.starting_players.all())

    statistics = [
        "Assists", "CleanSheets", "Conceded", "Dribbles", "Fouls", "Goals", "Matches",
        "MinutesPlayed", "Passes", "RedCards", "Saves", "Shoots", "ShootsOnTarget",
        "Tackles", "YellowCards"
    ]

    with transaction.atomic():
        existing_stats = PlayerMatchStatistic.objects.filter(match=match).values_list('player_id', flat=True)

        new_stats = []
        for player in starting_players:
            if player.id not in existing_stats:
                stats_data = {stat: 0 for stat in statistics}
                new_stats.append(
                    PlayerMatchStatistic(
                        player=player,
                        match=match,
                        statistics=stats_data
                    )
                )

        PlayerMatchStatistic.objects.bulk_create(new_stats)

    print(f"Generated Match Player Stats for {len(new_stats)} players.")


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


def generate_match_penalties(match):
    if not hasattr(match, 'penalties'):
        match_penalties, created = MatchPenalties.objects.get_or_create(
            match=match,
            defaults={
                "home_score": 0,
                "away_score": 0,
                "is_completed": False,
                "current_initiative": match.home_team,
            }
        )
        if created:
            print(f"Initialized penalties for match {match.id} with home team initiative.")
        else:
            print(f"Penalties already exist for match {match.id}.")
        return match_penalties
