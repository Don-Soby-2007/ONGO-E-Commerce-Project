# products/templatetags/product_extras.py
from django import template
import json

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Safely get dict[key] in templates (e.g., {{ mydict|get_item:keyvar }})"""
    if dictionary is None:
        return []
    return dictionary.get(key, [])


@register.filter
def to_json(value):
    """Convert Python object to JSON string for JS (use with |safe)"""
    return json.dumps(value)


@register.filter
def length_in_stock(variants):
    """Count how many variants are in stock"""
    return len([v for v in variants if getattr(v, 'stock', 0) > 0])


@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
