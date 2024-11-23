from django import template

register = template.Library()

@register.filter
def to_int(value):
    """Преобразува стойността в цяло число, ако е възможно."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0
