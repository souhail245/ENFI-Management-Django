from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='get_dict_item')
def get_dict_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}