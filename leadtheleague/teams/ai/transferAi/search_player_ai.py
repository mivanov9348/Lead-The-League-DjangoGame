import random
from decimal import Decimal

from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from game.utils.get_season_stats_utils import get_current_season
from messaging.utils.category_messages_utils import create_free_agent_transfer_message
from players.models import Position, Player
from staff.utils.agent_utils import process_agent_payment
from teams.models import TeamPlayer, Team
from teams.utils.team_finance_utils import buy_player_expense, team_expense
from teams.utils.update_team_stats import get_available_shirt_number
from transfers.models import Transfer
from transfers.utils import create_transfer


def search_player_decision_making():
    teams = Team.objects.filter(user__isnull=True).select_related('teamfinance')

    for team in teams:
        print(f"\n=== Checking {team.name} ===")

        team_finance = getattr(team, 'teamfinance', None)
        if not team_finance:
            print(f"{team.name}: No financial data found, skipping...")
            continue

        needed_position = ai_find_needed_position(team)
        if not needed_position:
            print(f"{team.name}: No reinforcement needed")
            continue

        best_team_player = ai_find_best_team_player(team, needed_position)
        best_market_player = ai_find_best_player(needed_position, team_finance.balance)

        if not best_market_player:
            print(f"{team.name}: No available players for {needed_position}")
            continue

        if team_finance.balance < Decimal(500000):
            print(f"{team.name}: Saving money, no transfer made.")
            continue

        if random.random() < 0.3:  # 30% шанс да не купува
            print(f"{team.name}: Chooses to not make a transfer.")
            continue

        if not best_team_player or best_market_player["rating"] > best_team_player["rating"]:
            send_offer_for_ai(team, best_market_player["player"], team_finance)
        else:
            print(
                f"{team.name}: {best_market_player['player'].first_name} {best_market_player['player'].last_name} is not an upgrade for {needed_position}")


def ai_find_needed_position(team):
    positions = ["GK", "DF", "MF", "ATT"]
    weakest_position = None
    weakest_value = float('inf')
    min_players_needed = {"GK": 2, "DF": 4, "MF": 4, "ATT": 3}

    for pos in positions:
        avg_strength = ai_calculate_position_strength(team, pos)
        player_count = TeamPlayer.objects.filter(team=team, player__position__abbreviation=pos).count()

        # Приоритетно търсим ако нямаме достатъчно играчи
        if player_count < min_players_needed[pos]:
            return pos

        # Ако няма недостиг, търсим най-слабата позиция
        if avg_strength < weakest_value:
            weakest_value = avg_strength
            weakest_position = pos

    return weakest_position if weakest_value < 70 else None


def ai_find_best_player(position_abbr, budget):
    position = get_object_or_404(Position, abbreviation=position_abbr)

    with transaction.atomic():  # Използваме транзакция, за да избегнем race conditions
        available_players = Player.objects.filter(
            position=position, is_free_agent=True, price__lte=budget
        ).select_for_update().order_by('-potential_rating')  # Заключваме записите за промяна

        best_player = available_players.first()
        if best_player:
            best_player.is_free_agent = False  # Предварително задаваме статуса
            best_player.save()

        return {"player": best_player, "rating": best_player.potential_rating} if best_player else None


def ai_find_best_team_player(team, position_abbr):
    position = get_object_or_404(Position, abbreviation=position_abbr)
    players = TeamPlayer.objects.filter(team=team, player__position=position).select_related('player')

    best_player = max(players, key=lambda p: p.player.potential_rating, default=None)
    return {"player": best_player.player, "rating": best_player.player.potential_rating} if best_player else None


def ai_calculate_position_strength(team, position_abbr):
    position = get_object_or_404(Position, abbreviation=position_abbr)
    players = TeamPlayer.objects.filter(team=team, player__position=position)

    if not players.exists():
        return 0

    return players.aggregate(Avg('player__potential_rating'))['player__potential_rating__avg']


def send_offer_for_ai(offering_team, player, team_finance):
    print(f'Attempting to sign {player.first_name} {player.last_name} for {offering_team.name}')

    if not offering_team or not player or not team_finance:
        print("Error: Missing required arguments (offering_team, player, or team_finance)")
        return

    try:
        offer_amount = player.price * Decimal(random.uniform(0.9, 1.1))
        print(f'Calculated offer amount: {offer_amount}')

        if team_finance.balance < offer_amount:
            print(f"{offering_team.name}: Not enough money for {player.first_name} {player.last_name} ({offer_amount})")
            return

        # team_finance.balance -= offer_amount
        # team_finance.total_expenses += offer_amount
        # team_finance.save()
        # print(f'Updated team finances: Balance={team_finance.balance}, Total Expenses={team_finance.total_expenses}')

        existing_team_player = TeamPlayer.objects.filter(player=player).first()
        if existing_team_player:
            print(
                f"{player.first_name} {player.last_name} is already assigned to {existing_team_player.team.name}, skipping transfer.")
            return

        team_expense(offering_team, offer_amount, f'Buy free agent {player.first_name} {player.last_name}')
        process_agent_payment(player.agent, offer_amount)

        team_player = TeamPlayer.objects.create(team=offering_team, player=player)
        print(f'Created TeamPlayer entry for {player.first_name} {player.last_name}')

        shirt_number = get_available_shirt_number(offering_team)
        print(f'Assigned shirt number: {shirt_number}')
        team_player.shirt_number = shirt_number
        team_player.save()

        current_season = get_current_season()
        print(f'Current season: {current_season}')

        create_transfer(offering_team, player, True)
        print(f'Transfer record created')

        player.is_free_agent = False
        Player.objects.filter(id=player.id).update(is_free_agent=False)
        print(f'Updated player status: Not a free agent')

        create_free_agent_transfer_message(player, offering_team)
        print(f'Transfer message created')

        print(
            f"{offering_team.name}: Signed {player.first_name} {player.last_name} as a free agent for {offer_amount}, wearing number {shirt_number}")

    except Exception as e:
        print(f'Error during transfer process: {e}')
