"""
Language switching views
"""
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .language_utils import set_language


@require_POST
def set_language_view(request):
    """Set user's preferred language"""
    language_code = request.POST.get('language', 'en')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    
    if set_language(request, language_code):
        lang_names = {'en': 'English', 'bn': 'বাংলা'}
        messages.success(request, f'Language changed to {lang_names.get(language_code, "English")}')
    else:
        messages.error(request, 'Invalid language selection')
    
    return redirect(next_url)
