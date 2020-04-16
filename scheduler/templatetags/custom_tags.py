import datetime

from django import template

register = template.Library()

@register.filter
def plus_days(value, days):
    return value + datetime.timedelta(days=days)