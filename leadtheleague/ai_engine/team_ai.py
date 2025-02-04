from ai_engine.q_learning import QLearningAI
from stadium.utils.get_stadium_stats import get_next_stadium_tier
from stadium.utils.stadium_upgrade_utils import upgrade_stadium
from teams.ai.coachAi.coachAi import CoachAI
from teams.ai.releaseAi.ReleaseAi import ReleaseAI
from teams.ai.stadiumAi.stadiumAi import StadiumAI
from teams.ai.transferAi.TransferAi import TransfersAI
from teams.utils.team_finance_utils import check_team_balance
from transfers.utils import is_transfer_day


class TeamAI:
    @staticmethod
    def process_team(team):
        ai = QLearningAI(team)
        state = ai.get_state()
        action = ai.choose_action(state)

        reward = 0

        if action == "hire_coach":
            CoachAI.assign_coach(team)
            reward = 8

        elif action == "train":
            CoachAI.manage_coaches_and_training(team)
            reward = 5


        elif action == "upgrade_stadium":
            stadium = team.stadium
            if stadium:
                next_tier = get_next_stadium_tier(stadium.tier)
                if next_tier and check_team_balance(team, next_tier.upgrade_cost):
                    if StadiumAI.should_upgrade(team, stadium, next_tier):
                        StadiumAI.perform_upgrade(team, stadium, next_tier)
                        reward = 10

        elif action == "buy_player":
            if is_transfer_day():
                TransfersAI.handle_transfers(team, team.teamfinance)
                reward = 15

        elif action == "sell_player":
            if is_transfer_day():
                ReleaseAI.manage_player_releases(team)
                reward = 10

        elif action == "save_money":
            reward = 2

        new_state = ai.get_state()
        ai.update_q_value(state, action, reward, new_state)
