import random
from decimal import Decimal
from django.db import transaction
from core.models import Nationality
from core.utils.names_utils import get_random_first_name, get_random_last_name
from finance.models import Bank
from finance.utils.bank_utils import distribute_income
from game.utils.settings_utils import get_setting_value
from players.models import Player
from players.utils.generate_player_utils import generate_free_agents
from staff.models import FootballAgent
from teams.utils.team_finance_utils import team_expense
from transfers.models import Transfer


def generate_agents():
    agents = []
    nationalities = Nationality.objects.all()
    print(f"Nationalities count: {len(nationalities)}")

    free_agents_count = 10
    for _ in range(free_agents_count):
        nationality = random.choice(nationalities)
        region = nationality.region

        first_name = get_random_first_name(region)
        last_name = get_random_last_name(region)

        age = random.randint(25, 60)
        starting_balance = get_setting_value("football_agents_starting_balance")
        print(f"Football agent starting balance: {starting_balance}")

        scouting_level = Decimal(str(random.uniform(1.0, 10.0))).quantize(Decimal('0.1'))
        print(f"Scouting level: {scouting_level}")

        agent = FootballAgent.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            balance=starting_balance,
            scouting_level=scouting_level
        )
        agents.append(agent)
        generate_free_agents(agent)
    return agents


def agent_sell_player(team, player):
    with transaction.atomic():
        agent = player.agent
        player.is_free_agent = False
        player.agent = None
        player.save()

    team_expense(team, player.price, f'{team.name} buy {player.first_name} {player.last_name}')
    if agent:
        process_agent_payment(agent, player.price)


def process_agent_payment(agent, price):
    with transaction.atomic():
        tax_rate_percentage = get_setting_value("free_agent_tax")
        tax_amount = price * Decimal(tax_rate_percentage / 100)

        agent_income = price - tax_amount
        agent.balance += agent_income
        agent.save()

        try:
            bank = Bank.objects.get(is_main=True)
            distribute_income(bank, tax_amount, f'Tax from Free Agent {agent.first_name} {agent.last_name}', None)
        except Bank.DoesNotExist:
            pass


def hire_agent_to_player(agent, player):
    if agent is None:
        agents = FootballAgent.objects.all()

        if not agents.exists():
            raise ValueError("Not enough agents!")

        agent = random.choice(agents)

    player.agent = agent
    player.is_free_agent = False
    player.save()

def agent_level_increase(agent, player):
    increment = min(0.5, (player.potential_rating / 100) * (player.price / 1000000))
    agent.scouting_level = min(10.0, agent.scouting_level + increment)
    agent.save()

from datetime import date

def agent_level_end_season_calculate(agent):
    """
    Recalculates the scouting level of a FootballAgent at the end of the season based on performance.
    """
    # Текущата година
    current_year = date.today().year

    # Намери трансфери, където играчите са били free agents и с агент == текущия
    sold_players = Transfer.objects.filter(
        player__is_free_agent=True,
        player__agent=agent,
        transfer_date__year=current_year
    )

    total_players = Player.objects.filter(agent=agent).count()

    performance_factor = len(sold_players) / (total_players + 1)

    decrement = max(-0.5, (performance_factor - 0.5) * -0.5)

    agent.scouting_level = max(0.0, agent.scouting_level + decrement)
    agent.save()

    print(f"Agent {agent.first_name} {agent.last_name}: New scouting level: {agent.scouting_level}")
