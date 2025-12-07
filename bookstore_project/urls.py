"""
URL Configuration for bookstore_project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# Add i18n patterns for language support
urlpatterns += i18n_patterns(
    path('', include('books.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    # path('rentals/', include('rentals.urls')),  # Rental UI disabled - models preserved
    path('support/', include('support.urls')),
    path('api/', include('books.api_urls')),
    prefix_default_language=False,
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "BookStore Administration"
admin.site.site_title = "BookStore Admin"
admin.site.index_title = "Welcome to BookStore Admin Panel"
