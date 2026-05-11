from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    try:
        return dictionary.get(key, {})
    except (AttributeError, TypeError):
        return {}
