from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Book Management
    path('books/', views.book_management, name='book_management'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('books/<int:pk>/delete/', views.delete_book, name='delete_book'),
    
    # Category Management
    path('categories/', views.category_management, name='category_management'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    
    # Order Management
    path('orders/', views.order_management, name='order_management'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Customer Management
    path('customers/', views.customer_management, name='customer_management'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    
    # Reviews Management
    path('reviews/', views.review_management, name='review_management'),
    path('reviews/<int:pk>/approve/', views.approve_review, name='approve_review'),
    path('reviews/<int:pk>/delete/', views.delete_review, name='delete_review'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/customers/', views.customer_report, name='customer_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
]
