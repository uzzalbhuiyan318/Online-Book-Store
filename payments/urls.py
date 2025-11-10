from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # bKash
    path('bkash/callback/', views.bkash_callback, name='bkash_callback'),
    path('bkash/execute/', views.bkash_execute, name='bkash_execute'),
    
    # Nagad
    path('nagad/callback/', views.nagad_callback, name='nagad_callback'),
    
    # Rocket
    path('rocket/callback/', views.rocket_callback, name='rocket_callback'),
    
    # SSLCommerz
    path('sslcommerz/success/', views.sslcommerz_success, name='sslcommerz_success'),
    path('sslcommerz/fail/', views.sslcommerz_fail, name='sslcommerz_fail'),
    path('sslcommerz/cancel/', views.sslcommerz_cancel, name='sslcommerz_cancel'),
    path('sslcommerz/ipn/', views.sslcommerz_ipn, name='sslcommerz_ipn'),
]
