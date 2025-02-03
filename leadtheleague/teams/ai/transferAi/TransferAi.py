import random
from decimal import Decimal

from teams.ai.transferAi.search_player_ai import ai_find_best_team_player, ai_find_needed_position, ai_find_best_player, \
    send_offer_for_ai


class TransfersAI:
    @staticmethod
    def handle_transfers(team, team_finance):
        print(f"{team.name}: Checking available transfer options.")
        if team_finance.balance < Decimal(500000):
            print(f"{team.name}: Insufficient budget (below $500,000), skipping transfers.")
            return
        needed_position = ai_find_needed_position(team)
        if not needed_position:
            print(f"{team.name}: No urgent transfer needs identified.")
            return
        best_team_player = ai_find_best_team_player(team, needed_position)
        best_market_player = ai_find_best_player(needed_position, team_finance.balance)
        if not best_market_player:
            print(f"{team.name}: No suitable players available for position: {needed_position}.")
            return
        if TransfersAI.should_make_transfer(team_finance, best_team_player, best_market_player):
            send_offer_for_ai(team, best_market_player["player"], team_finance)
        else:
            print(f"{team.name}: Decided not to buy {best_market_player['player'].first_name} {best_market_player['player'].last_name}.")

    @staticmethod
    def should_make_transfer(team_finance, best_team_player, best_market_player):
        if not best_team_player:
            print("No comparable player on the team for this position. Proceeding with the transfer.")
            return True
        rating_difference = best_market_player["rating"] - best_team_player["rating"]
        if rating_difference > 5:
            print(f"Significant rating improvement (+{rating_difference}). Proceeding with the transfer.")
            return True
        if team_finance.balance > Decimal(5_000_000) and random.random() > 0.4:
            print("Team has a high budget and passed a probabilistic check. Proceeding with the transfer.")
            return True
        if random.random() > 0.5:
            print("Passed a probabilistic check. Proceeding with the transfer.")
            return True
        print("Transfer decision criteria not met. Skipping the transfer.")
        return False