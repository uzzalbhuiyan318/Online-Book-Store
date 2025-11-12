from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Order Management
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Order Tracking
    path('track/', views.track_order, name='track_order'),
    path('track/<str:order_number>/', views.track_order, name='track_order'),
    
    # Coupon Management
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    
    # Invoice
    path('invoice/<str:order_number>/', views.invoice, name='invoice'),
    path('invoice/<str:order_number>/email/', views.email_invoice, name='email_invoice'),
]
