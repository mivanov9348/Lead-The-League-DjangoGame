from cups.models import SeasonCup
from finance.models import Fund
from finance.utils.fund_utils import add_fund_expense
from fixtures.models import CupFixture
from leagues.models import LeagueSeason, LeagueTeams
from teams.models import Team
from decimal import Decimal
from teams.utils.team_finance_utils import team_income


def end_of_season_fund_distribution(previous_season):
    distribute_league_fund(previous_season)
    distribute_cup_fund(previous_season)
    distribute_match_fund(previous_season)
    distribute_global_fund(previous_season)
    print(f'{previous_season.year} - {previous_season.season_number} funds are distributed!')


def calculate_team_percentages(num_teams):
    if num_teams <= 0:
        return []

    min_percentage = Decimal(1)
    max_percentage = Decimal(100) - (min_percentage * (num_teams - 1))

    if num_teams == 1:
        return [Decimal(100)]

    step = (max_percentage - min_percentage) / (num_teams - 1)
    percentages = [max_percentage - step * i for i in range(num_teams)]

    total_percentage = sum(percentages)
    normalized_percentages = [p / total_percentage * Decimal(100) for p in percentages]

    return normalized_percentages


def distribute_league_fund(season, league_fund_name='League Fund'):
    try:
        fund = Fund.objects.get(name=league_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {league_fund_name} doesn't exist.")

    print(f"Found fund: {fund.name} with balance: {fund.balance}")

    if fund.balance <= 0:
        raise ValueError("No Money in that Fund!")

    league_seasons = LeagueSeason.objects.filter(season=season, is_completed=True)
    if not league_seasons.exists():
        raise ValueError("No League Seasons!")

    print(f"Number of completed league seasons: {league_seasons.count()}")

    league_share = fund.balance / Decimal(league_seasons.count())
    print(f"League share per season: {league_share}")

    for league in league_seasons:
        print(f"Processing league: {league.league.name}")

        teams = league.teams.order_by('-points', '-goaldifference', '-goalscored')
        num_teams = teams.count()

        print(f"Number of teams in league: {num_teams}")

        if num_teams == 0:
            print("No teams in this league.")
            continue

        percentages = calculate_team_percentages(num_teams)
        print(f"Generated percentages: {percentages}")

        for team, percentage in zip(teams, percentages):
            team_share = league_share * (percentage / Decimal(100))
            print(f"Allocating {team_share} to team {team.team.name} ({percentage}%)")

            team_income(
                team=team.team,
                amount=team_share,
                description=f"Distribute {league_fund_name} for {league.league} ({team.team.name})"
            )

    print(f"Fund balance before expense: {fund.balance}")
    add_fund_expense(
        fund=fund,
        amount=fund.balance  # Използваме текущия баланс като обща сума за разпределение
    )
    print(f"Fund balance after expense: {fund.balance}")


def distribute_cup_fund(season, cup_fund_name="Cup Fund"):
    try:
        fund = Fund.objects.get(name=cup_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {cup_fund_name} does not exist.")

    if fund.balance <= 0:
        raise ValueError("The fund has no available balance for distribution.")

    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    if not season_cups.exists():
        raise ValueError("There are no completed cups for the current season.")

    # Distribute the fund evenly among the cups
    cup_share = fund.balance / Decimal(season_cups.count())

    for cup in season_cups:
        cup_fixtures = CupFixture.objects.filter(season_cup=cup, is_finished=True)

        if not cup_fixtures.exists():
            continue  # If no completed matches for the cup, skip to the next one

        team_match_counts = {}
        total_matches = 0

        # Count the number of matches played by each team
        for fixture in cup_fixtures:
            for team in [fixture.home_team, fixture.away_team]:
                team_match_counts[team] = team_match_counts.get(team, 0) + 1
                total_matches += 1

        if total_matches == 0:
            continue  # If no matches played, skip the cup

        for team, matches_played in team_match_counts.items():
            team_share = cup_share * (Decimal(matches_played) / Decimal(total_matches))

            team_income(
                team=team,
                amount=team_share,
                description=f"Distribute {cup_fund_name} for {cup.cup.name} ({team.name})"
            )

    add_fund_expense(
        fund=fund,
        amount=fund.balance  # Use the current balance as the total amount distributed
    )


def distribute_match_fund(season, match_fund_name="Match Fund"):
    try:
        fund = Fund.objects.get(name=match_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund '{match_fund_name}' does not exist.")

    if fund.balance <= 0:
        raise ValueError("The fund has no available balance for distribution.")

    team_scores = {}

    # Aggregate league team scores
    league_teams = LeagueTeams.objects.filter(league_season__season=season)
    for league_team in league_teams:
        team_scores[league_team.team] = (
                team_scores.get(league_team.team, 0) +
                league_team.points +
                league_team.goalscored
        )

    # Add points for progressing and champion teams in cups
    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    for cup in season_cups:
        for team in cup.progressing_teams.all():
            team_scores[team] = team_scores.get(team, 0) + 5  # 5 points for progressing
        if cup.champion_team:
            team_scores[cup.champion_team] = team_scores.get(cup.champion_team, 0) + 10  # 10 points for champion

    # Select top 10 teams based on scores
    top_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    total_score = sum(score for _, score in top_teams)

    if total_score == 0:
        raise ValueError("No scores available to distribute the match fund.")

    # Distribute fund based on team scores
    for team, score in top_teams:
        team_share = fund.balance * (Decimal(score) / Decimal(total_score))

        team_income(
            team=team,
            amount=team_share,
            description=f"Distribute {match_fund_name} for {team.name}"
        )

    add_fund_expense(
        fund=fund,
        amount=fund.balance
    )


def distribute_global_fund(global_fund_name="Global Fund"):
    try:
        fund = Fund.objects.get(name=global_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund '{global_fund_name}' does not exist.")

    if fund.balance <= 0:
        raise ValueError("The fund has no available balance for distribution.")

    teams = Team.objects.filter(is_active=True)
    if not teams.exists():
        raise ValueError("There are no active teams for fund distribution.")

    team_share = fund.balance / Decimal(teams.count())

    for team in teams:
        team_income(
            team=team,
            amount=team_share,
            description=f"Distribute {global_fund_name} for {team.name}"
        )

    add_fund_expense(
        fund=fund,
        amount=fund.balance
    )
