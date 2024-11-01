from django.contrib import messages
from accounts.models import CustomUser
from .models import InboxMessage


def get_recipient(recipient_id):
    try:
        return CustomUser.objects.get(id=recipient_id)
    except CustomUser.DoesNotExist:
        return None


def check_message_permissions(message, user):
    return message.receiver == user or message.sender == user


def send_message_success(request):
    messages.success(request, "Message sent successfully!")


def send_message_error(request, message):
    messages.error(request, message)

def get_received_messages(user):
    return InboxMessage.objects.filter(receiver=user)

def get_sended_messages(user):
    return InboxMessage.objects.filter(sender=user)
