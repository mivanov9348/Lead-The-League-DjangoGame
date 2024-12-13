from cups.models import Cup


def get_all_cups():
    cups = Cup.objects.prefetch_related('rules').all()
    return cups