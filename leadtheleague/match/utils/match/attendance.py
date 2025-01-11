import random

from teams.utils.team_finance_utils import team_match_profit


def calculate_match_attendance(match):
        max_capacity = 1000
        if match.stadium and match.stadium.capacity:
            max_capacity = match.stadium.capacity

        base_popularity = match.home_team.reputation + (match.away_team.reputation // 2)
        stadium_boost = match.stadium.tier.popularity_bonus if match.stadium and match.stadium.tier else 0

        raw_attendance = (base_popularity + stadium_boost) * random.uniform(1.8, 2.2)
        attendance = min(int(raw_attendance), max_capacity)
        match.attendance = attendance
        match.save()
        return attendance

def match_income(match, team):
        ticket_price = 10
        if match.stadium and match.stadium.ticket_price:
            ticket_price = match.stadium.ticket_price

        attendance = calculate_match_attendance(match)
        income = attendance * ticket_price
        team_match_profit(team, match, income, f'{match.home_team} - {match.away_team} (attendance: {attendance})')
