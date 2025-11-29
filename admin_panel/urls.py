from django.urls import path
from . import views_complete as views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Book Management
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('books/<int:pk>/quick-edit/', views.book_quick_edit, name='book_quick_edit'),
    path('books/bulk-action/', views.book_bulk_action, name='book_bulk_action'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Order Management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-status/', views.order_update_status, name='order_update_status'),
    
    # Customer Management
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    
    # Review Management
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/<int:pk>/approve/', views.review_approve, name='review_approve'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('reviews/bulk-action/', views.review_bulk_action, name='review_bulk_action'),
    
    # Coupon Management
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.coupon_add, name='coupon_add'),
    path('coupons/<int:pk>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:pk>/delete/', views.coupon_delete, name='coupon_delete'),
    
    # Rental Management
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/plans/', views.rental_plan_list, name='rental_plan_list'),
    path('rentals/plans/add/', views.rental_plan_add, name='rental_plan_add'),
    path('rentals/plans/<int:pk>/edit/', views.rental_plan_edit, name='rental_plan_edit'),
    path('rentals/plans/<int:pk>/delete/', views.rental_plan_delete, name='rental_plan_delete'),
    path('rentals/plans/bulk-action/', views.rental_plan_bulk_action, name='rental_plan_bulk_action'),
    path('rentals/plans/<int:pk>/toggle-status/', views.rental_plan_toggle_status, name='rental_plan_toggle_status'),
    path('rentals/settings/', views.rental_settings, name='rental_settings'),
    path('rentals/bulk-action/', views.rental_bulk_action, name='rental_bulk_action'),
    path('rentals/<str:rental_number>/', views.rental_detail, name='rental_detail'),
    path('rentals/<str:rental_number>/update-status/', views.rental_update_status, name='rental_update_status'),
    path('rentals/history/', views.rental_status_history_list, name='rental_status_history_list'),
    
    # Rental Feedback Management
    path('rentals/feedback/', views.rental_feedback_list, name='rental_feedback_list'),
    path('rentals/feedback/<int:pk>/approve/', views.rental_feedback_approve, name='rental_feedback_approve'),
    path('rentals/feedback/<int:pk>/respond/', views.rental_feedback_respond, name='rental_feedback_respond'),
    path('rentals/feedback/<int:pk>/delete/', views.rental_feedback_delete, name='rental_feedback_delete'),
    path('rentals/feedback/bulk-action/', views.rental_feedback_bulk_action, name='rental_feedback_bulk_action'),
    
    # Rental Notification Management
    path('rentals/notifications/', views.rental_notification_list, name='rental_notification_list'),
    path('rentals/notifications/bulk-action/', views.rental_notification_bulk_action, name='rental_notification_bulk_action'),
    
    # Banner Management
    path('banners/', views.banner_list, name='banner_list'),
    path('banners/add/', views.banner_add, name='banner_add'),
    path('banners/<int:pk>/edit/', views.banner_edit, name='banner_edit'),
    path('banners/<int:pk>/delete/', views.banner_delete, name='banner_delete'),
    
    # Support Management
    path('support/conversations/', views.support_conversation_list, name='support_conversation_list'),
    path('support/conversations/<str:conversation_id>/', views.support_conversation_detail, name='support_conversation_detail'),
    path('support/conversations/<str:conversation_id>/toggle-conversion/', views.support_conversation_toggle_conversion, name='support_conversation_toggle_conversion'),
    path('support/conversion-report/', views.support_conversion_report, name='support_conversion_report'),
    path('support/agents/', views.support_agent_list, name='support_agent_list'),
    path('support/agents/add/', views.support_agent_add, name='support_agent_add'),
    path('support/agents/<int:pk>/edit/', views.support_agent_edit, name='support_agent_edit'),
    path('support/quick-replies/', views.quick_reply_list, name='quick_reply_list'),
    path('support/quick-replies/add/', views.quick_reply_add, name='quick_reply_add'),
    path('support/quick-replies/<int:pk>/edit/', views.quick_reply_edit, name='quick_reply_edit'),
    path('support/chat-settings/', views.chat_settings, name='chat_settings'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/customers/', views.customer_report, name='customer_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    
    # Export Functions
    path('export/orders/', views.export_orders_csv, name='export_orders_csv'),
    path('export/customers/', views.export_customers_csv, name='export_customers_csv'),
    path('export/books/', views.export_books_csv, name='export_books_csv'),
    # Gift Form / Gift Locations Management
    path('gifts/', views.gift_form_list, name='gift_form_list'),
    path('gifts/<int:pk>/', views.gift_form_detail, name='gift_form_detail'),
    path('gifts/cities/', views.gift_city_list, name='gift_city_list'),
    path('gifts/cities/add/', views.gift_city_add, name='gift_city_add'),
    path('gifts/cities/<int:pk>/edit/', views.gift_city_edit, name='gift_city_edit'),
    path('gifts/areas/', views.gift_area_list, name='gift_area_list'),
    path('gifts/areas/add/', views.gift_area_add, name='gift_area_add'),
    path('gifts/areas/<int:pk>/edit/', views.gift_area_edit, name='gift_area_edit'),
    path('gifts/areas/<int:pk>/delete/', views.gift_area_delete, name='gift_area_delete'),
    path('gifts/zones/', views.gift_zone_list, name='gift_zone_list'),
    path('gifts/zones/add/', views.gift_zone_add, name='gift_zone_add'),
    path('gifts/zones/<int:pk>/edit/', views.gift_zone_edit, name='gift_zone_edit'),
    path('gifts/zones/<int:pk>/delete/', views.gift_zone_delete, name='gift_zone_delete'),
    path('gifts/occasions/', views.gift_occasion_list, name='gift_occasion_list'),
    path('gifts/occasions/add/', views.gift_occasion_add, name='gift_occasion_add'),
    path('gifts/occasions/<int:pk>/edit/', views.gift_occasion_edit, name='gift_occasion_edit'),
]
