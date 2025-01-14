import json
import os
import random
from django.db import transaction
from europeancups.models import EuropeanCupTeam
from fixtures.models import LeagueFixture
from game.models import MatchSchedule
from game.utils.get_season_stats_utils import get_current_season
from leadtheleague import settings
from match.utils.match.attendance import calculate_match_attendance, match_income
from match.utils.match.retrieval import get_match_by_fixture
from messaging.utils.category_messages_utils import create_league_matchday_message, create_league_champion_message
from teams.models import Team
from .models import League, LeagueSeason, LeagueTeams


def generate_leagues_season(season):
    leagues = League.objects.all()
    for league in leagues:
        if not LeagueSeason.objects.filter(league=league, season=season).exists():
            LeagueSeason.objects.create(league=league, season=season)


def get_all_leagues():
    return League.objects.all()


def get_all_season_leagues(season):
    return LeagueSeason.objects.filter(season=season)


def get_selected_league(league_id):
    league = League.objects.filter(id=league_id).first()
    return league


def get_standings_for_league(league):
    league_season = LeagueSeason.objects.filter(
        league=league
    ).order_by('-season__year').first()

    if not league_season:
        return []

    return LeagueTeams.objects.filter(
        league_season=league_season
    ).select_related('team').order_by(
        '-points', '-goaldifference', '-goalscored', 'goalconceded'
    )


def get_teams_by_league(league_id):
    return Team.objects.filter(league_id=league_id) if league_id else Team.objects.none()


def check_and_mark_league_seasons_completed():
    with transaction.atomic():
        active_league_seasons = LeagueSeason.objects.filter(is_completed=False)

        for league_season in active_league_seasons:
            if not league_season.fixtures.filter(is_finished=False).exists():
                league_season.is_completed = True
                league_season.save()

def populate_teams_for_season(season):
    json_path = os.path.join(settings.BASE_DIR, "static/data/leagues_and_teams.json")

    try:
        with open(json_path, "r") as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        print(f"JSON file not found.")
        return

    league_seasons = LeagueSeason.objects.filter(season=season)

    for league_season in league_seasons:
        league_name = league_season.league.name

        if league_name not in json_data:
            print(f"No data for {league_name} in the JSON file.")
            continue

        teams = json_data[league_name]
        for team_data in teams:
            team, _ = Team.objects.get_or_create(
                name=team_data["name"],
                defaults={
                    "abbreviation": team_data["name"][:3].upper(),
                    "reputation": team_data["reputation"],
                    "nationality": league_season.league.nationality,
                },
            )

            LeagueTeams.objects.get_or_create(
                league_season=league_season,
                team=team,
                defaults={
                    "matches": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goalscored": 0,
                    "goalconceded": 0,
                    "goaldifference": 0,
                    "points": 0,
                },
            )

        print(f"Teams populated for {league_name}.")


def simulate_day_league_fixtures(match_day):
    with transaction.atomic():
        active_seasons = LeagueSeason.objects.filter(season__match_schedule__date=match_day)

        for league_season in active_seasons:
            league = league_season.league

            fixtures = LeagueFixture.objects.filter(
                league_season__league=league, date=match_day, is_finished=False
            )

            if not fixtures.exists():
                continue

            for fixture in fixtures:
                home_goals = random.randint(0, 7)
                away_goals = random.randint(0, 7)

                fixture.home_goals = home_goals
                fixture.away_goals = away_goals
                fixture.is_finished = True

                if home_goals > away_goals:
                    fixture.winner = fixture.home_team
                elif away_goals > home_goals:
                    fixture.winner = fixture.away_team

                fixture.save()

                try:
                    match = get_match_by_fixture(fixture)
                except ValueError:
                    continue

                match.home_goals = home_goals
                match.away_goals = away_goals
                match.is_played = True
                match.current_minute = 90

                attendance = calculate_match_attendance(match)
                match.attendance = attendance
                match.save()

                match_income(match, match.home_team)

            update_standings_from_fixtures(league_season, fixtures)
            create_league_matchday_message(league_season)

        check_and_mark_league_seasons_completed()


def update_standings_from_fixtures(fixtures):
    print("Updating standings based on fixtures...")
    for fixture in fixtures:
        if isinstance(fixture, LeagueFixture):  # Проверяваме дали фикстурата е от тип LeagueFixture
            league_season = fixture.league_season
            home_team_record = LeagueTeams.objects.get(
                league_season=league_season, team=fixture.home_team
            )
            away_team_record = LeagueTeams.objects.get(
                league_season=league_season, team=fixture.away_team
            )

            # Актуализация на статистики
            home_team_record.matches += 1
            away_team_record.matches += 1

            home_team_record.goalscored += fixture.home_goals
            home_team_record.goalconceded += fixture.away_goals
            away_team_record.goalscored += fixture.away_goals
            away_team_record.goalconceded += fixture.home_goals

            if fixture.home_goals > fixture.away_goals:
                home_team_record.wins += 1
                away_team_record.losses += 1
                home_team_record.points += 3
            elif fixture.away_goals > fixture.home_goals:
                away_team_record.wins += 1
                home_team_record.losses += 1
                away_team_record.points += 3
            else:
                home_team_record.draws += 1
                away_team_record.draws += 1
                home_team_record.points += 1
                away_team_record.points += 1

            home_team_record.goaldifference = (
                home_team_record.goalscored - home_team_record.goalconceded
            )
            away_team_record.goaldifference = (
                away_team_record.goalscored - away_team_record.goalconceded
            )

            # Запазваме промените
            home_team_record.save()
            away_team_record.save()

    print("Standings update completed.")


def assign_league_champions(season):
    if not season:
        season = get_current_season()
        return

    played_league_days = MatchSchedule.objects.filter(
        season=season,
        is_league_day_assigned=True,
        is_played=True
    )

    if not played_league_days.exists():
        print("Няма изиграни лиги през активния сезон.")
        return

    league_seasons = LeagueSeason.objects.filter(season=season)

    for league_season in league_seasons:
        league_teams = league_season.teams.all()

        if not league_teams.exists():
            print(f"Няма отбори за лига {league_season.league.name}.")
            continue

        champion_team = league_teams.order_by('-points', '-goaldifference', '-goalscored').first()

        if champion_team:
            league_season.champion_team = champion_team.team
            league_season.is_completed = True
            league_season.save()
            create_league_champion_message()
            print(f"Шампион на лигата {league_season.league.name}: {champion_team.team.name}")
        else:
            print(f"Неуспешно определяне на шампиона за лига {league_season.league.name}.")


def promote_league_teams_to_europe(new_season, new_european_cup_season, european_cups, cup_champions):
    leagues = League.objects.all()
    added_teams = []

    for league in leagues:
        previous_league_season = league.seasons.filter(is_completed=True).order_by('-season__year').first()
        if not previous_league_season:
            continue

        qualifiers_count = league.euro_qualifiers
        if qualifiers_count <= 0:
            continue

        top_teams = previous_league_season.teams.order_by('-points', '-goaldifference', '-goalscored')[:qualifiers_count]
        qualified_teams = []

        for team in top_teams:
            if len(qualified_teams) >= qualifiers_count:
                break
            if team.team not in cup_champions and team.team not in qualified_teams:
                qualified_teams.append(team.team)

        added_teams.extend(qualified_teams)

        for cup in european_cups:
            for team in qualified_teams:
                EuropeanCupTeam.objects.create(
                    team=team,
                    european_cup_season=new_european_cup_season
                )
            print(f"Added {', '.join([team.name for team in qualified_teams])} from {league.name} to {cup.name}.")

    return added_teams

