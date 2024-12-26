from django.db.models import Q
from django.shortcuts import get_object_or_404
from messaging.models import UserMessageStatus, SystemMessage

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