from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from fixtures.models import LeagueFixture, CupFixture, EuropeanCupFixture
from game.utils.get_season_stats_utils import get_current_season
from match.models import Match


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