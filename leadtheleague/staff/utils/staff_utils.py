from django.core.exceptions import ValidationError


def validate_age(value):
    if value < 18 or value > 60:
        raise ValidationError("Age must be between 18 and 60.")
