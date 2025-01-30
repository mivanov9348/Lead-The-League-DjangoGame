import random
from decimal import Decimal


def player_training(coach, player):
    # Вземаме важните показатели
    coach_rating = Decimal(coach.rating)  # Уверяваме се, че coach_rating е Decimal
    determination = Decimal(random.randint(8, 15))  # Генерираме стойност за determination
    work_rate = Decimal(random.randint(8, 15))  # Генерираме стойност за work_rate

    # Базова формула за тренировъчния резултат
    base_impact = (coach_rating * Decimal(1.5)) + (determination * Decimal(0.7)) + (work_rate * Decimal(0.7))

    # Добавяме случайност за реализъм (фактор между 0.9 и 1.1)
    random_factor = Decimal(random.uniform(0.9, 1.1))  # Превръщаме random_factor в Decimal
    training_impact = base_impact * random_factor

    # Ограничава се в разумен диапазон (0.5 до 10.0), за да има минимално въздействие
    training_impact = Decimal(max(0.5, min(training_impact, 10))).quantize(Decimal("0.01"))

    # Връщаме резултата за разпределяне по атрибутите
    return {
        "training_impact": training_impact,
        "details": f"Training by {coach} for {player}: Impact {training_impact} (Determination: {determination}, Work Rate: {work_rate})"
    }