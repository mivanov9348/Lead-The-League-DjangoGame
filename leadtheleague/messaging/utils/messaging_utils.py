from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from messaging.models import UserMessageStatus, SystemMessage

def get_user_and_global_messages(user):
    return SystemMessage.objects.filter(Q(is_global=True) | Q(recipient=user))

def create_system_message(recipient, title, message, is_global):
    return SystemMessage.objects.create(
        recipient=recipient,
        title=title,
        preview=message[:30],
        message=message,
        date_sent=  now(),
        is_global=is_global
    )
