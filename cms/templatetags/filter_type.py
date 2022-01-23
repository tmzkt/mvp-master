from django import template

register = template.Library()


@register.filter
def get_type(value):
    return isinstance(value, list)


@register.filter
def filter_range(value):
    return range(value)
