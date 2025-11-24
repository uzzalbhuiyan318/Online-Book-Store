"""
Language utility functions for Bangla support
"""

def get_current_language(request):
    """Get current language from session or default to 'en'"""
    return request.session.get('django_language', 'en')


def set_language(request, language_code):
    """Set language preference in session"""
    if language_code in ['en', 'bn']:
        request.session['django_language'] = language_code
        return True
    return False


def get_field_value(obj, field_name, language='en'):
    """
    Get field value in specified language
    Falls back to English if Bangla version is not available
    
    Args:
        obj: Model instance
        field_name: Base field name (e.g., 'title', 'name', 'description')
        language: 'en' or 'bn'
    
    Returns:
        Field value in specified language or fallback to English
    """
    if language == 'bn':
        bn_field = f"{field_name}_bn"
        if hasattr(obj, bn_field):
            bn_value = getattr(obj, bn_field, None)
            if bn_value:
                return bn_value
    
    # Fallback to English
    if hasattr(obj, field_name):
        return getattr(obj, field_name, '')
    
    return ''


def get_language_display(language_code):
    """Get language display name"""
    languages = {
        'en': 'English',
        'bn': 'বাংলা'
    }
    return languages.get(language_code, 'English')
