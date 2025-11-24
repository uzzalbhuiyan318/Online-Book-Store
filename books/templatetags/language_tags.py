"""
Template tags for Bangla language support
"""
from django import template
from books.language_utils import get_field_value, get_current_language

register = template.Library()


@register.simple_tag(takes_context=True)
def get_lang_field(context, obj, field_name):
    """
    Get field value in current language
    Usage: {% get_lang_field book 'title' %}
    """
    request = context.get('request')
    if request:
        language = get_current_language(request)
    else:
        language = 'en'
    
    return get_field_value(obj, field_name, language)


@register.filter
def bn_field(obj, field_name):
    """
    Get Bangla field value if available, otherwise English
    Usage: {{ book|bn_field:'title' }}
    """
    return get_field_value(obj, field_name, 'bn')


@register.filter
def en_field(obj, field_name):
    """
    Get English field value
    Usage: {{ book|en_field:'title' }}
    """
    return get_field_value(obj, field_name, 'en')


@register.simple_tag(takes_context=True)
def localized_field(context, obj, field_name):
    """
    Get field value in current language based on session
    Usage: {% localized_field book 'title' %}
    """
    request = context.get('request')
    if request:
        language = get_current_language(request)
        return get_field_value(obj, field_name, language)
    return get_field_value(obj, field_name, 'en')
