import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='tojson')
def tojson(value):
    """
    Convert a Python object to JSON string suitable for HTML attributes.
    Uses json.dumps to ensure proper JSON format with double quotes.
    """
    if value is None:
        return '[]'

    try:
        # json.dumps outputs valid JSON with double quotes
        # ensure_ascii=False to preserve special chars like ø, å, etc.
        result = json.dumps(value, ensure_ascii=False)
        return mark_safe(result)
    except (TypeError, ValueError):
        return '[]'
