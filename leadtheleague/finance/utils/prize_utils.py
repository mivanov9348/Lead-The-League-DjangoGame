from accounts.models import CustomUser
from cups.models import SeasonCup
from finance.models import Fund
from finance.utils.fund_utils import add_fund_expense
from fixtures.models import CupFixture
from leagues.models import LeagueSeason, LeagueTeams
from messaging.utils.category_messages_utils import create_prize_fund_message
from teams.models import Team
from decimal import Decimal
from teams.utils.team_finance_utils import team_income


def end_of_season_fund_distribution(previous_season):
    results = {
        "total_sum": Decimal(0),
        "league_fund": Decimal(0),
        "cup_fund": Decimal(0),
        "global_fund": Decimal(0),
        "match_fund": Decimal(0),
        "teams": []
    }

    results["league_fund"] = distribute_league_fund(previous_season, results)
    results["cup_fund"] = distribute_cup_fund(previous_season, results)
    results["match_fund"] = distribute_match_fund(previous_season, results)
    results["global_fund"] = distribute_global_fund(results)

    results["total_sum"] = (
        results["league_fund"] +
        results["cup_fund"] +
        results["match_fund"] +
        results["global_fund"]
    )

    users = CustomUser.objects.filter(team__isnull=False)
    for user in users:
        create_prize_fund_message(user, previous_season, results)

    print(f'{previous_season.year} - {previous_season.season_number} funds distributed!')
    return results

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

def distribute_league_fund(season, results, league_fund_name='League Fund'):
    try:
        fund = Fund.objects.get(name=league_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {league_fund_name} doesn't exist.")

    if fund.balance <= 0:
        raise ValueError("No money in that fund!")

    league_seasons = LeagueSeason.objects.filter(season=season, is_completed=True)
    if not league_seasons.exists():
        raise ValueError("No League Seasons!")

    league_share = fund.balance / Decimal(league_seasons.count())
    league_total = Decimal(0)

    for league in league_seasons:
        teams = league.teams.order_by('-points', '-goaldifference', '-goalscored')
        if not teams.exists():
            continue

        percentages = calculate_team_percentages(teams.count())

        for team, percentage in zip(teams, percentages):
            team_share = league_share * (percentage / Decimal(100))
            league_total += team_share
            results["teams"].append({
                "team_name": team.team.name,
                "team_prize": team_share,
                "fund": league_fund_name
            })

            team_income(
                team=team.team,
                amount=team_share,
                description=f"Distribute {league_fund_name} for {league.league} ({team.team.name})"
            )

    add_fund_expense(fund=fund, amount=fund.balance)
    return league_total


def distribute_cup_fund(season, results, cup_fund_name="Cup Fund"):
    try:
        fund = Fund.objects.get(name=cup_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {cup_fund_name} does not exist.")

    if fund.balance <= 0:
        raise ValueError("No money in that fund!")

    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    cup_share = fund.balance / Decimal(season_cups.count())
    cup_total = Decimal(0)

    for cup in season_cups:
        cup_fixtures = CupFixture.objects.filter(season_cup=cup, is_finished=True)
        team_match_counts = {}

        for fixture in cup_fixtures:
            for team in [fixture.home_team, fixture.away_team]:
                team_match_counts[team] = team_match_counts.get(team, 0) + 1

        total_matches = sum(team_match_counts.values())
        if total_matches == 0:
            continue

        for team, matches_played in team_match_counts.items():
            team_share = cup_share * (Decimal(matches_played) / Decimal(total_matches))
            cup_total += team_share
            results["teams"].append({
                "team_name": team.name,
                "team_prize": team_share,
                "fund": cup_fund_name
            })

            team_income(
                team=team,
                amount=team_share,
                description=f"Distribute {cup_fund_name} for {cup.cup.name} ({team.name})"
            )

    add_fund_expense(fund=fund, amount=fund.balance)
    return cup_total


def distribute_match_fund(season, results, match_fund_name="Match Fund"):
    try:
        fund = Fund.objects.get(name=match_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {match_fund_name} does not exist.")

    if fund.balance <= 0:
        raise ValueError("No money in that fund!")

    team_scores = {}
    league_teams = LeagueTeams.objects.filter(league_season__season=season)
    for league_team in league_teams:
        team_scores[league_team.team] = (
            team_scores.get(league_team.team, 0) +
            league_team.points +
            league_team.goalscored
        )

    total_score = sum(team_scores.values())
    match_total = Decimal(0)

    for team, score in team_scores.items():
        team_share = fund.balance * (Decimal(score) / Decimal(total_score))
        match_total += team_share
        results["teams"].append({
            "team_name": team.name,
            "team_prize": team_share,
            "fund": match_fund_name
        })

        team_income(
            team=team,
            amount=team_share,
            description=f"Distribute {match_fund_name} for {team.name}"
        )

    add_fund_expense(fund=fund, amount=fund.balance)
    return match_total


def distribute_global_fund(results, global_fund_name="Global Fund"):
    try:
        fund = Fund.objects.get(name=global_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {global_fund_name} does not exist.")

    if fund.balance <= 0:
        raise ValueError("No money in that fund!")

    teams = Team.objects.filter(is_active=True)
    team_share = fund.balance / Decimal(teams.count())
    global_total = Decimal(0)

    for team in teams:
        global_total += team_share
        results["teams"].append({
            "team_name": team.name,
            "team_prize": team_share,
            "fund": global_fund_name
        })

        team_income(
            team=team,
            amount=team_share,
            description=f"Distribute {global_fund_name} for {team.name}"
        )

    add_fund_expense(fund=fund, amount=fund.balance)
    return global_total