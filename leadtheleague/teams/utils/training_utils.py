import random
from decimal import Decimal

def player_training(coach, player):
    coach_rating = Decimal(coach.rating) / Decimal(10.0)

    determination = Decimal(random.uniform(0.5, 1.5))  # Случайна стойност между 0.5 и 1.5
    work_rate = Decimal(random.uniform(0.5, 1.5))  # Случайна стойност между 0.5 и 1.5

    base_impact = (coach_rating * Decimal(2.0)) + (determination * Decimal(0.5)) + (work_rate * Decimal(0.5))

    random_factor = Decimal(random.uniform(0.8, 1.2))

    training_impact = base_impact * random_factor

    training_impact = Decimal(max(0.1, min(training_impact, 5.0))).quantize(Decimal("0.01"))

    return {
        "training_impact": training_impact,
        "details": f"Training by {coach} for {player}: Impact {training_impact} (Determination: {determination}, Work Rate: {work_rate})"
    }