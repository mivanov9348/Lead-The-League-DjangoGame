from cups.models import SeasonCup
from finance.models import Fund
from finance.utils.fund_utils import add_fund_expense
from fixtures.models import CupFixture
from leagues.models import LeagueSeason, LeagueTeams
from teams.models import Team
from decimal import Decimal
from teams.utils.team_finance_utils import team_income


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

        min_percentage = Decimal(1)
        max_percentage = Decimal(100) - (min_percentage * (num_teams - 1))

        step = (max_percentage - min_percentage) / (num_teams - 1)
        percentages = [max_percentage - step * i for i in range(num_teams)]

        print(f"Generated percentages: {percentages}")

        total_percentage = sum(percentages)
        normalized_percentages = [p / total_percentage * Decimal(100) for p in percentages]

        print(f"Normalized percentages: {normalized_percentages}")

        for team, percentage in zip(teams, normalized_percentages):
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
        amount=fund.balance  # Използвай текущия баланс като обща сума за разпределение
    )
    print(f"Fund balance after expense: {fund.balance}")



def distribute_cup_fund(season, cup_fund_name="Cup Fund"):
    try:
        fund = Fund.objects.get(name=cup_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {cup_fund_name} не съществува.")

    if fund.balance <= 0:
        raise ValueError("Фондът няма налични средства за разпределяне.")

    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    if not season_cups.exists():
        raise ValueError("Няма завършени купи за текущия сезон.")

    # Разпределение на фонда между купите
    cup_share = fund.balance / Decimal(season_cups.count())

    for cup in season_cups:
        cup_fixtures = CupFixture.objects.filter(season_cup=cup, is_finished=True)

        if not cup_fixtures.exists():
            continue  # Ако няма завършени мачове за купата, продължи със следващата

        team_match_counts = {}
        total_matches = 0

        # Събиране на броя изиграни мачове за всеки отбор
        for fixture in cup_fixtures:
            for team in [fixture.home_team, fixture.away_team]:
                team_match_counts[team] = team_match_counts.get(team, 0) + 1
                total_matches += 1

        if total_matches == 0:
            continue  # Ако няма изиграни мачове, пропусни купата

        # Разпределение на средствата спрямо броя изиграни мачове
        for team, matches_played in team_match_counts.items():
            team_share = cup_share * (Decimal(matches_played) / Decimal(total_matches))

            team_income(
                team=team,
                amount=team_share,
                description=f"Distribute {cup_fund_name} for {cup.cup.name} ({team.name})"
            )

    add_fund_expense(
        fund=fund,
        amount=fund.balance  # Използвай текущия баланс като обща сума за разпределение
    )


def distribute_global_fund(global_fund_name="Global Fund"):
    try:
        fund = Fund.objects.get(name=global_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {global_fund_name} не съществува.")

    if fund.balance <= 0:
        raise ValueError("Фондът няма налични средства за разпределяне.")

    teams = Team.objects.filter(is_active=True)
    if not teams.exists():
        raise ValueError("Няма активни отбори за разпределение на фонда.")

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

def distribute_match_fund(season, match_fund_name="Match Fund"):
    try:
        fund = Fund.objects.get(name=match_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {match_fund_name} не съществува.")

    if fund.balance <= 0:
        raise ValueError("Фондът няма налични средства за разпределяне.")

    team_scores = {}

    league_teams = LeagueTeams.objects.filter(league_season__season=season)
    for team in league_teams:
        team_scores[team.team] = team_scores.get(team.team, 0) + team.points + team.goalscored

    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    for cup in season_cups:
        for team in cup.progressing_teams.all():
            team_scores[team] = team_scores.get(team, 0) + 5  # 5 точки за прогресиране
        if cup.champion_team:
            team_scores[cup.champion_team] = team_scores.get(cup.champion_team, 0) + 10  # 10 точки за шампион

    top_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    total_score = sum(score for _, score in top_teams)

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
