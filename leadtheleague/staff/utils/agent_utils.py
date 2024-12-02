import random
from players.models import Nationality
from players.utils.generate_player_utils import get_player_random_first_and_last_name, generate_free_agents
from staff.models import Agent

def generate_agents(modeladmin, request, queryset):
    agents = []
    nationalities = Nationality.objects.all()

    for _ in range(20):
        nationality = random.choice(nationalities)
        region = nationality.region

        first_name, last_name = get_player_random_first_and_last_name(region)
        age = random.randint(25, 60)

        agent = Agent.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            balance=100000
        )
        generate_free_agents(agent)
        agents.append(agent)

    modeladmin.message_user(request, f"{len(agents)} Agents is successfull.")
    return agents
