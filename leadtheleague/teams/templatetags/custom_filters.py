from django import template
register = template.Library()

@register.filter
def get_stat_value(stats, stat_name):
    if not stats:
        return "N/A"
    last_season = max(stats.keys(), default=None)
    if last_season and stat_name in stats[last_season]:
        return stats[last_season][stat_name]
    return "N/A"
