from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter(name='get_dict_item')
def get_dict_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}

@register.filter
def divided_by(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def stringformat(value, arg):
    """
    Formats the value like a 'str' filter but with the specified format.
    """
    return str(value)

@register.filter
def get_dict_item(dictionary, key):
    """Retourne l'élément d'un dictionnaire pour une clé donnée."""
    if dictionary is None:
        return None  # Retourne None si le dictionnaire est vide
    return dictionary.get(key)

@register.filter
def replace(value, arg):
    """
    Remplace toutes les occurrences de arg[0] par arg[1] dans value
    Usage: {{ value|replace:"_," }}
    """
    if len(arg.split(',')) != 2:
        return value
    what, to = arg.split(',')
    return value.replace(what, to)