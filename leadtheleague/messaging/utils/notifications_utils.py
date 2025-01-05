from accounts.models import CustomUser
from match.models import Match
from django.utils.timezone import now
from messaging.models import Notification

def create_match_notifications(match_date):
    print(f"Processing match date: {match_date}")
    if not hasattr(match_date, 'date'):
        raise ValueError(f"Invalid match_date: {match_date}. Expected datetime.date or datetime.datetime.")

    played_matches = Match.objects.filter(match_date=match_date.date, is_played=True)

    if not played_matches.exists():
        print(f"No played matches found for {match_date.date}.")
        return

    match_results = "\n".join([
        f"{match.home_team.name} {match.home_goals} : {match.away_goals} {match.away_team.name}"
        for match in played_matches
    ])

    content = f"Results for {match_date.date}:\n{match_results}"

    users = CustomUser.objects.all()
    notifications = [
        Notification(user=user, content=content, created_at=now())
        for user in users
    ]

    Notification.objects.bulk_create(notifications)
    print(f"Notifications created for {len(users)} users with results for {len(played_matches)} matches.")

def create_new_user_notification(user, team):
    content = (
        f"Welcome to the game, {user.username}!\n\n"
        f"You are now the manager of {team.name}. Prepare your strategy, "
        f"train your players, and lead your team to victory!"
    )

    notification = Notification.objects.create(
        user=user,
        content=content,
        created_at=now()
    )
    print(f"Notification created for user {user.username}: {content}")
    return notification