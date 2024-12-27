import random
from decimal import Decimal
from django.db import transaction
from core.models import Nationality
from core.utils.names_utils import get_random_first_name, get_random_last_name
from finance.models import Bank
from finance.utils.bank_utils import distribute_income
from game.utils.settings_utils import get_setting_value
from players.utils.generate_player_utils import generate_free_agents
from staff.models import Agent
from teams.utils.team_finance_utils import team_expense


def generate_agents():
    agents = []
    nationalities = Nationality.objects.all()

    free_agents_count = 10

    for _ in range(free_agents_count):
        nationality = random.choice(nationalities)
        region = nationality.region

        first_name = get_random_first_name(region)
        last_name = get_random_last_name(region)

        age = random.randint(25, 60)
        starting_balance = get_setting_value("free_agents_starting_balance")

        agent = Agent.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            balance=starting_balance
        )
        agents.append(agent)

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
        agents = Agent.objects.all()

        if not agents.exists():
            raise ValueError("Not enough agents!")

        agent = random.choice(agents)

    player.agent = agent
    player.is_free_agent = False
    player.save()
