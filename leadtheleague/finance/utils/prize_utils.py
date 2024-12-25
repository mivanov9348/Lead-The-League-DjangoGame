from cups.models import SeasonCup
from finance.models import Fund
from fixtures.models import CupFixture
from leagues.models import LeagueSeason, LeagueTeams
from teams.models import TeamTransaction, TeamFinance, Team
from decimal import Decimal

def distribute_league_fund(season, league_fund_name='League Fund'):
    try:
        fund = Fund.objects.get(name=league_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {league_fund_name} doesn't exist.")

    if fund.balance <= 0:
        raise ValueError("No Money in that Fund!")

    league_seasons = LeagueSeason.objects.filter(season=season, is_completed=True)
    if not league_seasons.exists():
        raise ValueError("No League Seasons!")

    league_share = fund.balance / Decimal(league_seasons.count())

    for league in league_seasons:
        teams = league.teams.order_by('-points', '-goaldifference', '-goalscored')
        num_teams = teams.count()

        # Генерирай процентите за дялове (гарантирано >= 0)
        base_percentage = Decimal(50)
        step = Decimal(5)
        percentages = [max(base_percentage - step * i, Decimal(0)) for i in range(num_teams)]

        # Нормализирай процентите
        total_percentage = sum(percentages)
        if total_percentage == 0:
            raise ValueError("Total percentage cannot be zero.")
        normalized_percentages = [p / total_percentage * Decimal(100) for p in percentages]

        for team, percentage in zip(teams, normalized_percentages):
            team_share = league_share * (percentage / Decimal(100))

            if team_share < Decimal(0):
                team_share = Decimal(0)  # Увери се, че няма отрицателни стойности

            TeamTransaction.objects.create(
                team=team.team,
                bank=fund.bank,
                type='IN',
                amount=team_share,
                description=f"Distribute {league_fund_name} for {league.league} ({team.team.name})"
            )

            team_finance = TeamFinance.objects.get(team=team.team)
            team_finance.balance += team_share
            team_finance.total_income += team_share
            team_finance.save()

    # Обнови фонда
    fund.total_expense += fund.balance
    fund.balance = 0
    fund.save()


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

            TeamTransaction.objects.create(
                team=team,
                bank=fund.bank,
                type='IN',
                amount=team_share,
                description=f"Distribute {cup_fund_name} for {cup.cup.name} ({team.name})"
            )

            # Актуализация на финансите на отбора
            team_finance = TeamFinance.objects.get(team=team)
            team_finance.balance += team_share
            team_finance.total_income += team_share
            team_finance.save()

    # Актуализация на фонда
    fund.total_expense += fund.balance
    fund.balance = 0
    fund.save()



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
        TeamTransaction.objects.create(
            team=team,
            bank=fund.bank,
            type='IN',
            amount=team_share,
            description=f"Distribute {global_fund_name} for {team.name}"
        )

        team_finance = TeamFinance.objects.get(team=team)
        team_finance.balance += team_share
        team_finance.total_income += team_share
        team_finance.save()

    fund.total_expense += fund.balance
    fund.balance = 0
    fund.save()


def distribute_match_fund(season, match_fund_name="Match Fund"):
    # 1. Намери фонда
    try:
        fund = Fund.objects.get(name=match_fund_name)
    except Fund.DoesNotExist:
        raise ValueError(f"Fund {match_fund_name} не съществува.")

    if fund.balance <= 0:
        raise ValueError("Фондът няма налични средства за разпределяне.")

    # 2. Създай рейтинг за отборите
    team_scores = {}

    # Лига: Точки и голове
    league_teams = LeagueTeams.objects.filter(league_season__season=season)
    for team in league_teams:
        team_scores[team.team] = team_scores.get(team.team, 0) + team.points + team.goalscored

    # Купа: Прогрес
    season_cups = SeasonCup.objects.filter(season=season, is_completed=True)
    for cup in season_cups:
        for team in cup.progressing_teams.all():
            team_scores[team] = team_scores.get(team, 0) + 5  # 5 точки за прогресиране
        if cup.champion_team:
            team_scores[cup.champion_team] = team_scores.get(cup.champion_team, 0) + 10  # 10 точки за шампион

    # 3. Нормализирай и избери топ 10 отбора
    top_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    total_score = sum(score for _, score in top_teams)

    # 4. Разпределение на фонда
    for team, score in top_teams:
        team_share = fund.balance * (Decimal(score) / Decimal(total_score))

        # Създай транзакция
        TeamTransaction.objects.create(
            team=team,
            bank=fund.bank,
            type='IN',
            amount=team_share,
            description=f"Distribute {match_fund_name} for {team.name}"
        )

        team_finance = TeamFinance.objects.get(team=team)
        team_finance.balance += team_share
        team_finance.total_income += team_share
        team_finance.save()

    fund.total_expense += fund.balance
    fund.balance = 0
    fund.save()
