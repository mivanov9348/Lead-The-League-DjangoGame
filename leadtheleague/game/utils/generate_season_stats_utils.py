from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from fixtures.utils import generate_fixtures
from game.models import Season
from leagues.models import League
from match.utils.generate_match_stats_utils import generate_matches_for_season
from players.utils.generate_player_utils import generate_youth_player
from teams.utils.get_team_stats_utils import get_all_teams

def create_new_season(year, season_number, start_date, match_time):
    try:
        season = Season.objects.get(year=year, season_number=season_number)
        return season
    except ObjectDoesNotExist:
        try:
            season = Season(year=year, season_number=season_number, start_date=start_date, match_time=match_time)
            season.save()

            # generate fixtures
            leagues = League.objects.all()
            for league in leagues:
                generate_fixtures(start_date, league, season, match_time)

            # generate 5 youth players
            teams = get_all_teams()
            for team in teams:
                for i in range(5):
                    generate_youth_player(team)

            generate_matches_for_season(season)
        except IntegrityError as e:
            print("Foreign key error in Match creation:", e)
            raise
        return season

