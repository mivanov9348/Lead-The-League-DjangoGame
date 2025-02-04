import random

from ai_engine.models import QTable


class QLearningAI:
    def __init__(self, team, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.team = team
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon  # ❌ Тук имаше запетая, която правеше self.gamma да е tuple

    def get_state(self):
        return f'{self.team.teamfinance.balance}_{self.team.reputation}_{self.team.match_stats.count()}'

    def get_possible_actions(self):
        return ["hire_coach", "train", "upgrade_stadium", "buy_player", "sell_player", "save_money"]

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.get_possible_actions())

        q_values = QTable.objects.filter(team=self.team, state=state)
        if q_values.exists():
            return max(q_values, key=lambda q: q.q_value).action
        return random.choice(self.get_possible_actions())

    def update_q_value(self, state, action, reward, new_state):
        q_entry, created = QTable.objects.get_or_create(team=self.team, state=state, action=action)
        old_q_value = q_entry.q_value

        future_rewards = QTable.objects.filter(team=self.team, state=new_state)
        max_future_q = max([q.q_value for q in future_rewards], default=0)

        new_q_value = (1 - self.alpha) * old_q_value + self.alpha * (reward + self.gamma * max_future_q)
        q_entry.q_value = new_q_value
        q_entry.save()