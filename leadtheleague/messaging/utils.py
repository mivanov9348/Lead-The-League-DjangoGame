from django.db.models import Q
from messaging.models import ChatMessage

def get_last_message_preview(user, contact_user):
    # Намираме последното съобщение от дадения контакт (или изпратено, или получено)
    last_message = ChatMessage.objects.filter(
        (Q(sender=user) & Q(recipient=contact_user)) |
        (Q(sender=contact_user) & Q(recipient=user))
    ).order_by('-timestamp').first()

    # Връщаме първите 15 символа от съобщението, ако има такова
    if last_message:
        return last_message.content[:15]  # Връщаме само първите 15 знака
    return ''