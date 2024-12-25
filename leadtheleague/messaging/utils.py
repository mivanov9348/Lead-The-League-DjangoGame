import random
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from accounts.models import CustomUser
from europeancups.models import EuropeanCupSeason
from messaging.models import MessageTemplate, SystemMessage, UserMessageStatus


def get_user_and_global_messages(user):
    return SystemMessage.objects.filter(Q(is_global=True) | Q(recipient=user))

def get_message_preview(message):
    preview_text = message.content[:15]

    message.preview = preview_text
    message.save()

    return preview_text


def get_user_message_status(user, message):
    user_message_status = get_object_or_404(UserMessageStatus, user=user, message=message)
    return user_message_status.is_read


def make_message_is_read(user, message):
    user_message_status = get_object_or_404(UserMessageStatus, user=user, message=message)
    user_message_status.is_read = True
    user_message_status.save()


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

def get_european_cup_champion_placeholder():
    latest_season = EuropeanCupSeason.objects.filter(champion__isnull=False).order_by('-season').first()
    if not latest_season:
        raise ValueError("No European Cup Champion found in the database.")
    return {'team_name': latest_season.champion.name}

CATEGORY_HANDLERS = {
    "european cup champion": get_european_cup_champion_placeholder,

}

def create_message(category, placeholders, is_global=False, recipient=None):
    if category in CATEGORY_HANDLERS:
        category_placeholders = CATEGORY_HANDLERS[category]()
        placeholders.update(category_placeholders)
        print(f"Combined placeholders: {placeholders}")

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
        recipient=None if is_global else recipient,
        title=template.title,
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=is_global
    )

    create_user_message_status(system_message, is_global, recipient)

    return system_message