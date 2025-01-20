from unittest import TestCase
from unittest.mock import patch

from core.models import Nationality
from players.models import Position, Player
from staff.models import FootballAgent
from staff.utils.agent_utils import hire_agent_to_player


class AgentScoutingTests(TestCase):

    def setUp(self):
        self.agent = FootballAgent.objects.create(
            first_name='John',
            last_name='Morich',
            age=23,
            balance=500000.00,
            scouting_level=6.7
        )

        self.position = Position.objects.create(name='Attacker')

    def test_agent_creation(self):
        agent = self.agent

        self.assertEqual(agent.first_name, 'John')
        self.assertEqual(agent.last_name, 'Morich')
        self.assertEqual(agent.age, 23)
        self.assertEqual(agent.balance, 500000)
        self.assertEqual(agent.scouting_level, 6.7)

    def test_agent_fields_type(self):
        agent = self.agent

        self.assertIsInstance(agent.first_name, str)
        self.assertIsInstance(agent.last_name, str)
        self.assertIsInstance(agent.age, int)
        self.assertIsInstance(agent.balance, float)
        self.assertIsInstance(agent.scouting_level, float)


class HireAgentToPlayerTests(TestCase):

    def setUp(self):
        self.agent = FootballAgent.objects.create(
            first_name='John',
            last_name='Doe',
            age=35,
            balance=500000.00,
            scouting_level=8.2
        )

        self.player = Player.objects.create(
            first_name='Mike',
            last_name='Smith',
            age=25,
            position=Position.objects.filter().first(),
            nationality=Nationality.objects.filter().first(),
            is_free_agent=True
        )

    def test_hire_agent_to_player_with_given_agent(self):
        hire_agent_to_player(self.agent, self.player)

        self.assertEqual(self.player.agent, self.agent)
        self.assertFalse(self.player.is_free_agent)

    def test_hire_agent_to_player_with_no_given_agent(self):
        with patch('random.choice') as mock_random_choice:
            mock_random_choice.return_value = self.agent

            hire_agent_to_player(None, self.player)

            self.assertEqual(self.player.agent, self.agent)
            self.assertFalse(self.player.is_free_agent)

    def test_hire_agent_to_player_no_agents_available(self):
        FootballAgent.objects.all().delete()

        with self.assertRaises(ValueError):
            hire_agent_to_player(None, self.player)
