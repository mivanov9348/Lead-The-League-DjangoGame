import os

import django
from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import Nationality
from players.models import Position, Player
from staff.models import FootballAgent
from decimal import Decimal

os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
django.setup()

class PlayerModelTests(TestCase):

    def setUp(self):
        self.nationality = Nationality.objects.create(name='Spanish', region='Europe')
        self.position = Position.objects.create(name='Attacker')
        self.agent = FootballAgent.objects.create(first_name='John', last_name='Doe', age=35, balance=10000, scouting_level=5.5)

    def test_player_creation(self):
        player = Player.objects.create(
            first_name='Lionel',
            last_name='Messi',
            nationality=self.nationality,
            age=32,
            price=Decimal('1000000.00'),
            position=self.position,
        )

        self.assertEqual(player.first_name, 'Lionel')
        self.assertEqual(player.last_name, 'Messi')
        self.assertEqual(player.nationality.name, 'Spanish')
        self.assertEqual(player.age, 32)
        self.assertEqual(str(player.price), '1000000.00')
        self.assertEqual(player.position.name, 'Attacker')
        self.assertEqual(player.is_active, True)
        self.assertEqual(player.is_youth, False)
        self.assertEqual(player.is_free_agent, False)
        self.assertEqual(player.potential_rating, 1.0)
        self.assertIsNone(player.agent)

    def test_default_values(self):
        player = Player.objects.create(
            first_name='Cristiano',
            last_name='Ronaldo',
            nationality=self.nationality,
            age=35,
            price=Decimal('500000.00'),
            position=self.position,
        )

        self.assertTrue(player.is_active)
        self.assertFalse(player.is_youth)
        self.assertFalse(player.is_free_agent)
        self.assertEqual(player.potential_rating, 1.0)

    def test_age_validation(self):
        player_valid = Player(
            first_name='Valid',
            last_name='Player',
            nationality=self.nationality,
            age=14,
            price=Decimal('100000.00'),
            position=self.position,
        )
        player_valid.full_clean()  # Това ще повдигне изключение, ако възрастта не е валидна

        with self.assertRaises(ValidationError):
            player_invalid = Player(
                first_name='Invalid',
                last_name='Player',
                nationality=self.nationality,
                age=13,
                price=Decimal('100000.00'),
                position=self.position,
            )
            player_invalid.full_clean()

        with self.assertRaises(ValidationError):
            player_invalid = Player(
                first_name='Invalid',
                last_name='Player',
                nationality=self.nationality,
                age=100,
                price=Decimal('100000.00'),
                position=self.position,
            )
            player_invalid.full_clean()

    def test_player_agent_association(self):
        player = Player.objects.create(
            first_name='Neymar',
            last_name='Jr',
            nationality=self.nationality,
            age=28,
            price=Decimal('2000000.00'),
            position=self.position,
            agent=self.agent,
        )

        self.assertEqual(player.agent.first_name, 'John')
        self.assertEqual(player.agent.last_name, 'Doe')
        self.assertEqual(player.agent.balance, 10000)
        self.assertEqual(player.agent.scouting_level, 5.5)

    def test_foreign_key_associations(self):
        player = Player.objects.create(
            first_name='Karim',
            last_name='Benzema',
            nationality=self.nationality,
            age=34,
            price=Decimal('700000.00'),
            position=self.position,
        )

        self.assertEqual(player.nationality.name, 'Spanish')
        self.assertEqual(player.position.name, 'Attacker')
