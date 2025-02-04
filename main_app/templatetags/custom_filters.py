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
        return {}  # Retourner un dictionnaire vide plutôt que None
    return dictionary.get(key, {})

@register.filter
def split(value, separator=','):
    """Divise une chaîne en liste selon le séparateur donné"""
    return value.split(separator)

@register.filter
def get_events_at_time(events_dict, time):
    """Récupère les événements pour une heure donnée"""
    if events_dict is None:
        return []  # Retourner une liste vide si le dictionnaire est None
    
    event = events_dict.get(time)
    return [event] if event else []

@register.filter
def get_duration_slots(event):
    """Calcule le nombre de créneaux horaires occupés par un événement"""
    if event.heure_debut and event.heure_fin:
        duration = (event.heure_fin.hour - event.heure_debut.hour) * 2
        if event.heure_fin.minute - event.heure_debut.minute >= 30:
            duration += 1
        return duration
    return 1

@register.filter
def multiply(value, arg):
    return int(value) * int(arg)

