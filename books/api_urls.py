"""
REST API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'books', api_views.BookViewSet, basename='book')
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')
router.register(r'orders', api_views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
