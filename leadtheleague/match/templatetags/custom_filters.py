from django import template

register = template.Library()

@register.filter
def get_key(dictionary, key):
    """Връща стойността от речника за даден ключ."""
    return dictionary.get(key, 0)
