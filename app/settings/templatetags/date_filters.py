from django import template
from datetime import date

register = template.Library()

@register.filter
def make_date(value, year, month, day):
    """
    Создает объект date из строки даты
    """
    try:
        return date(int(year), int(month), int(day))
    except (ValueError, TypeError):
        return date.today()

@register.filter
def lookup(dictionary, key):
    """
    Кастомный фильтр для доступа к словарю по ключу
    """
    try:
        return dictionary.get(key, [])
    except (AttributeError, TypeError):
        return []
