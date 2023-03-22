from django import template

register = template.Library()


@register.filter
def get_by_key(obj, key):
    return obj.get(key)
