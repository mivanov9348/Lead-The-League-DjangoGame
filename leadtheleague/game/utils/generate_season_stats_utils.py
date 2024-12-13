from django.db import IntegrityError, transaction
from cups.models import Cup
from cups.utils.generate_cup_fixtures import generate_season_cup_and_fixtures
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import League
from match.utils.generate_match_stats_utils import generate_matches_for_season
from players.utils.generate_player_utils import generate_youth_player
from teams.utils.get_team_stats_utils import get_all_teams

def create_new_season(year, season_number, start_date, match_time):
    try:
        with transaction.atomic():
            season, created = Season.objects.get_or_create(
                year=year,
                season_number=season_number,
                defaults={'start_date': start_date, 'match_time': match_time}
            )

            if not created:
                return season

            # Генериране на фикстури за лиги
            leagues = League.objects.all()
            for league in leagues:
                generate_fixtures(start_date, league, season, match_time)

            # Генериране на играчи
            teams = get_all_teams()
            for team in teams:
                for _ in range(5):
                    generate_youth_player(team)

            # Генериране на купи
            cups = Cup.objects.all()
            for cup in cups:
                try:
                    generate_season_cup_and_fixtures(cup)
                except Exception as e:
                    print(f"Error generating cup {cup.name}: {e}")

            # Генериране на мачове
            generate_matches_for_season(season)

        return season
    except IntegrityError as e:
        print("Error during transaction:", e)
        return None