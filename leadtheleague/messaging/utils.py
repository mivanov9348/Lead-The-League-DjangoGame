from accounts.models import CustomUser
from europeancups.models import EuropeanCupSeason
from messaging.models import UserMessageStatus

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

