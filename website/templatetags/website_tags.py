from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def joinby(value, arg):
    return mark_safe(arg.join(value))
