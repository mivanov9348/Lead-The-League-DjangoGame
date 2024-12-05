from django.db.models import Q
from messaging.models import ChatMessage


def get_message_preview(message):
    preview_text = message.content[:15]  # Връщаме само първите 15 знака

    message.preview = preview_text
    message.save()

    return preview_text
