from django.core.exceptions import ObjectDoesNotExist
from django.templatetags.static import static
from teams.models import Team, TeamFinance


def team_info(request):
    if request.user.is_authenticated:
        try:
            user_team = Team.objects.get(user=request.user)
        except ObjectDoesNotExist:
            # Ако няма отбор за потребителя
            return {
                'team_name': 'No Team',
                'team_finance': {'balance': 0},
            }

        try:
            team_finance = TeamFinance.objects.get(team=user_team)
        except ObjectDoesNotExist:
            # Ако няма финансови данни за отбора
            return {
                'team_name': user_team.name,
                'team_finance': {'balance': 0},
            }

        return {
            'team_name': user_team.name,
            'team_finance': {'balance': team_finance.balance},
        }

    return {
        'team_name': 'Guest',
        'team_finance': {'balance': 0},
    }



def backgrounds(request):
    backgrounds = [
        static(f'images/{i}.jpg') for i in range(1, 21)
    ]
    return {'backgrounds': backgrounds}
