from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # how this isn't builtin, idk
    return dictionary.get(key)
