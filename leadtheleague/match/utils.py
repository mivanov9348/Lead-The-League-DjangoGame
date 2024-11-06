from fixtures.models import Fixture
from game.models import Season
from players.models import Player, PlayerMatchStatistic, Statistic, Position, PositionAttribute, PlayerAttribute
from .models import Match, EventTemplate
from datetime import datetime
import random


def generate_matches_for_season(season):
    fixtures = Fixture.objects.filter(season=season)

    for fixture in fixtures:
        Match.objects.create(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            division=fixture.division,
            date=datetime.combine(fixture.date, fixture.match_time),
            home_goals=fixture.home_goals,
            away_goals=fixture.away_goals,
            is_played=fixture.is_finished,
            season=season
        )


def update_matches(dummy_team, new_team):
    home_matches = Match.objects.filter(home_team=dummy_team)
    away_matches = Match.objects.filter(away_team=dummy_team)

    for match in home_matches:
        match.home_team = new_team
        match.save()

    for match in away_matches:
        match.away_team = new_team
        match.save()


def get_current_minute(request):
    current_minute = request.session.get('current_minute', 0)
    increment = random.randint(1, 5)
    current_minute += increment

    if current_minute > 90:
        current_minute = 90

    return current_minute


def generate_player_match_stats():
    current_season = Season.objects.filter(is_ended=False).first()  # Вземете първия несвършен сезон
    if not current_season:
        print("Няма активен сезон.")
        return

    matches = Match.objects.filter(season=current_season)
    players = Player.objects.all()

    for match in matches:
        for player in players:
            if player.team in [match.home_team, match.away_team]:
                for statistic in Statistic.objects.all():
                    PlayerMatchStatistic.objects.create(
                        player=player,
                        match=match,
                        statistic=statistic,
                        value=0
                    )


def get_match_team_initiative(match):
    return match.home_team if match.is_home_initiative else match.away_team

def choose_event_random_player(team):
    players = team.players.filter(is_starting=True)
    selected_player = random.choice(players)
    return selected_player

def get_match_position_attributes(position):
    position_attributes = PositionAttribute.objects.filter(position=position)
    attributes_dict = {pa.attribute: pa for pa in position_attributes}
    print(f"Position attributes for {position}: {attributes_dict}")
    return attributes_dict

def determine_action(player, position):

    #
    # actions = []
    #
    # # Определяне на действията на базата на атрибутите на играча
    # if player_attributes.get("Finishing", 0) > 15:
    #     actions.append("Score")
    # elif player_attributes.get("Finishing", 0) > 10:
    #     actions.append("Shoot")
    #
    # if player_attributes.get("Passing", 0) > 15:
    #     actions.append("Pass")
    # elif player_attributes.get("Passing", 0) < 10:
    #     actions.append("Lose possession")
    #
    # if position not in ['Goalkeeper']:
    #     if player_attributes.get("Tackling", 0) > 10:
    #         actions.append("Tackle")
    #     if player_attributes.get("Aggression", 0) > 15:
    #         actions.append("Yellow Card")
    #
    # if position == 'Goalkeeper':
    #     if player_attributes.get("Reflexes", 0) > 15:
    #         actions.append("Save")
    #     if player_attributes.get("Positioning", 0) > 10:
    #         actions.append("Concede")
    #
    # # Избор на случайно действие
    # selected_action = random.choice(actions) if actions else "No Action"
    # print(f"Determined action for {player.name}: {selected_action}")
    # return selected_action
    pass


def get_event_template(action):
    event_templates = EventTemplate.objects.filter(event_type=action)
    selected_template = random.choice(event_templates) if event_templates else None
    print(f"Event template for action '{action}': {selected_template.template_text if selected_template else 'None'}")
    return selected_template


def player_action(player):
    position = player.position  # Предполага се, че играчът има атрибут position
    print(f"Processing action for player: {player.name}, Position: {position}")
    action = determine_action(player, position)

    event_template = get_event_template(action)

    if event_template:
        event_text = event_template.template_text.format(player_name=player.name)
        print(f"Event generated: {event_text}")
        # Логика за запис на събитието или допълнителна обработка
        return event_text  # Можеш да промениш какво връща функцията

    return f"{player.name} performs an action: {action} but no event was found."
