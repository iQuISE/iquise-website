from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

def swap_regex(expr,string,val):
    to_replace = [(m.start(),m.end()) for m in re.finditer(expr,string)]
    to_replace.reverse()
    for [start,end] in to_replace:
        string = string[0:start] + val + string[end:]
    return string

@register.filter
def joinby(value, arg):
    return mark_safe(arg.join(value))

@register.filter
def embedded_video(video):
    html = video.engine.html_template
    html = swap_regex(r'{{(.*?[I|i][D|d].*?)}}',html,video.video_id)
    return mark_safe(html)