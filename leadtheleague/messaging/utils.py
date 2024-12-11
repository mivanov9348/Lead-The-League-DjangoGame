import random

from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from accounts.models import CustomUser
from messaging.models import MessageTemplate, SystemMessage, UserMessageStatus


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


def create_message(category, placeholders, is_global=False, recipient=None):
    templates = MessageTemplate.objects.filter(category=category)

    if not templates.exists():
        raise ValueError(f"No templates found for category '{category}'")

    template = random.choice(templates)

    message = template.message
    for key, value in placeholders.items():
        placeholder = f"{{{{ {key} }}}}"
        message = message.replace(placeholder, str(value))

    system_message = SystemMessage.objects.create(
        recipient=recipient if not is_global else None,
        title=template.title,
        preview=message[:30],
        message=message,
        date_sent=now(),
        is_global=is_global
    )

    create_user_message_status(system_message, is_global, recipient)

    return system_message
