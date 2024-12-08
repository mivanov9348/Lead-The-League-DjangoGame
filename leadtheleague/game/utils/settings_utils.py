from game.models import Settings


def get_setting_value(key):
    try:
        return Settings.objects.get(key=key).value
    except Settings.DoesNotExist:
        raise ValueError(f"Setting with key '{key}' does not exist!")

