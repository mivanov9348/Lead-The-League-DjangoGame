import random
from django.utils.timezone import now
from accounts.models import CustomUser
from messaging.models import UserMessageStatus, SystemMessage, MessageTemplate
from messaging.utils.placeholders_utils import get_free_agent_transfer_placeholders, get_new_coach_placeholders, \
    get_league_matchday_placeholders, \
    get_cup_matchday_placeholders, get_european_cup_champion_placeholder, get_league_champion_placeholder, \
    get_cup_champion_placeholder, get_team_to_team_transfer_placeholder, get_release_player_placeholders, \
    get_send_offer_placeholder


def create_message_for_new_season(category, placeholders, is_global=True):
    templates = MessageTemplate.objects.filter(category=category)

    if not templates:
        raise ValueError(f"No templates found for category '{category}'")

    template = random.choice(templates)
    print(f"Template message before formatting: {template.message}")

    try:
        message = template.message.format(**{k: str(v) for k, v in placeholders.items()})
    except KeyError as e:
        raise ValueError(f"Missing placeholder for key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_user_message_status(system_message, is_global, recipient):
    if is_global:
        users = CustomUser.objects.all()
        user_message_statuses = [
            UserMessageStatus(user=user, message=system_message)
            for user in users
        ]
        UserMessageStatus.objects.bulk_create(user_message_statuses)
    elif recipient:
        UserMessageStatus.objects.create(user=recipient, message=system_message)


def create_message_for_new_manager(category, placeholders, is_global=False):
    templates = MessageTemplate.objects.filter(category=category)

    if not templates:
        raise ValueError(f"No templates found for category '{category}'")

    template = random.choice(templates)
    print(f"Template message before formatting: {template.message}")

    try:
        message = template.message.format(**{k: str(v) for k, v in placeholders.items()})
    except KeyError as e:
        raise ValueError(f"Missing placeholder for key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_team_to_team_transfer_message(player, from_team, to_team, amount):
    placeholders = get_team_to_team_transfer_placeholder(player, from_team, to_team, amount)

    template = MessageTemplate.objects.filter(category='team to team transfer').order_by('?').first()
    if not template:
        raise ValueError("No templates found for 'team to team transfer' category.")

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message

def create_send_offer_message(player, from_team, to_team, amount):
    placeholders = get_send_offer_placeholder(player, from_team, to_team, amount)

    template = MessageTemplate.objects.filter(category='send offer').order_by('?').first()
    if not template:
        raise ValueError("No templates found for 'send offer' category.")

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=to_team.user,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=False
    )

    create_user_message_status(system_message, is_global=False, recipient=to_team.user)

    return system_message

def create_free_agent_transfer_message(player, team):
    placeholders = get_free_agent_transfer_placeholders(player, team)

    templates = MessageTemplate.objects.filter(category='free agent transfer')
    if not templates.exists():
        raise ValueError("No templates found for 'free agent transfer' category.")

    template = random.choice(templates)

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=team.user,
        title=template.title,
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=False
    )

    create_user_message_status(system_message, is_global=False, recipient=team.user)

    return system_message

def create_release_player_message(player, team):
    placeholders = get_release_player_placeholders(player, team)

    templates = MessageTemplate.objects.filter(category='release player')
    if not templates.exists():
        raise ValueError("No templates found for 'release player' category.")

    template = random.choice(templates)

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=team.user,
        title=template.title,
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=False
    )

    create_user_message_status(system_message, is_global=False, recipient=team.user)

    return system_message

def create_new_coach_message(coach, team):
    placeholders = get_new_coach_placeholders(coach, team)

    templates = MessageTemplate.objects.filter(category='new coach')
    if not templates.exists():
        raise ValueError("No templates found for 'new coach' category.")

    template = random.choice(templates)

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=team.user,
        title=template.title,
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=False
    )

    create_user_message_status(system_message, is_global=False, recipient=team.user)
    print(f'system message: {system_message}')

    return system_message


def create_league_matchday_message(league_season):
    placeholders = get_league_matchday_placeholders(league_season)

    templates = MessageTemplate.objects.filter(category='League Matchday')
    if not templates.exists():
        raise ValueError("No templates found for 'League Matchday' category.")

    template = random.choice(templates)

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_cup_matchday_message(season_cup):
    placeholders = get_cup_matchday_placeholders(season_cup)

    templates = MessageTemplate.objects.filter(category='Cup Matchday')
    if not templates.exists():
        raise ValueError("No templates found for 'Cup Matchday' category.")

    template = random.choice(templates)

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_league_champion_message():
    placeholders = get_league_champion_placeholder()

    template = MessageTemplate.objects.filter(category='League Champion').order_by('?').first()
    if not template:
        raise ValueError("No templates found for 'League Champion' category.")

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_cup_champion_message():
    placeholders = get_cup_champion_placeholder()

    template = MessageTemplate.objects.filter(category='Cup Champion').order_by('?').first()
    if not template:
        raise ValueError("No templates found for 'Cup Champion' category.")

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message


def create_european_cup_champion_message():
    placeholders = get_european_cup_champion_placeholder()

    template = MessageTemplate.objects.filter(category='European Cup Champion').order_by('?').first()
    if not template:
        raise ValueError("No templates found for 'European Cup Champion' category.")

    try:
        message = template.message.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder key: {e}. Provided placeholders: {placeholders}")

    system_message = SystemMessage.objects.create(
        recipient=None,
        title=template.title.format(**placeholders),
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=True
    )

    create_user_message_status(system_message, is_global=True, recipient=None)

    return system_message
