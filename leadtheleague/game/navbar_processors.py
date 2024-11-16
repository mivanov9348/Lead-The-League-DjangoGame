from teams.models import Team

def user_team(request):
    """Context processor за извличане на името на отбора на текущия потребител"""
    if request.user.is_authenticated:
        # Променяме 'manager' на 'user', за да използваме правилното поле
        team = Team.objects.filter(user=request.user).first()  # или друга логика
        return {'user_team': team}  # Връща името на отбора
    return {'user_team': None}  # Ако потребителят не е свързан с отбор
