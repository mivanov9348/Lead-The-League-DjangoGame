import random
from decimal import InvalidOperation, Decimal

from teams.utils.team_finance_utils import team_match_profit


def calculate_match_attendance(match):
    if not match.stadium:
        raise ValueError("No current stadium.")

    try:
        max_capacity = match.stadium.capacity
        home_popularity = match.home_team.reputation if match.home_team.reputation else 1
        away_popularity = match.away_team.reputation if match.away_team.reputation else 1
        base_popularity = (0.7 * home_popularity) + (0.3 * away_popularity)
        stadium_bonus = match.stadium.tier.popularity_bonus * 50 if match.stadium.tier else 0
        max_reputation = 10000
        normalized_popularity = (base_popularity + stadium_bonus) / max_reputation
        fill_rate = min(normalized_popularity, 1.0)
        raw_attendance = fill_rate * max_capacity * random.uniform(0.85, 1.15)
        attendance = min(int(raw_attendance), max_capacity)

        match.attendance = attendance
        match.save()
        return attendance
    except Exception as e:
        print(f"Error calculating attendance for match {match}: {e}")
        raise


from decimal import Decimal, InvalidOperation


def calculate_match_income(match, team):
    try:
        # Проверка за стадион и цена на билет
        ticket_price = 10
        if match.stadium and match.stadium.ticket_price:
            ticket_price = match.stadium.ticket_price
            print(f"Ticket price from stadium: {ticket_price}")
            try:
                ticket_price = Decimal(ticket_price)
            except InvalidOperation:
                print(f"Invalid ticket_price: {ticket_price}")
                raise ValueError(f"Invalid ticket price: {ticket_price}")
        else:
            print(f"Using default ticket price: {ticket_price}")
            ticket_price = Decimal(ticket_price)

        # Изчисляване на присъствие на мача
        attendance = calculate_match_attendance(match)
        print(f"Calculated attendance: {attendance}")
        if not isinstance(attendance, int) or attendance < 0:
            print(f"Invalid attendance value: {attendance}")
            raise ValueError(f"Invalid attendance value: {attendance}")

        # Изчисление на доходите
        try:
            income = Decimal(attendance) * ticket_price
            print(f"Calculated income: {income}")
        except InvalidOperation:
            print(f"Invalid operation when calculating income: attendance={attendance}, ticket_price={ticket_price}")
            raise

        match.match_income = income
        print(f"Match income before saving: {match.match_income}")
        match.save()
        print(f"Match income saved: {match.match_income}")

        print(f'income1: {income}')
        team_match_profit(
            team,
            match,
            income,
            f'{match.home_team} - {match.away_team} (attendance: {attendance})'
        )
        print(f"Team profit function called with income: {income}")
    except InvalidOperation as e:
        print(f"Decimal operation error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
