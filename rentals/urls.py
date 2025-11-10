from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    # Rental Plans
    path('plans/', views.rental_plans, name='rental_plans'),
    
    # Book Rental
    path('rent/<slug:slug>/', views.book_rental_detail, name='book_rental_detail'),
    path('rent/<slug:slug>/create/', views.create_rental, name='create_rental'),
    
    # My Rentals
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    path('rental/<str:rental_number>/', views.rental_detail, name='rental_detail'),
    
    # Rental Actions
    path('rental/<str:rental_number>/renew/', views.renew_rental, name='renew_rental'),
    path('rental/<str:rental_number>/return/', views.return_rental, name='return_rental'),
    path('rental/<str:rental_number>/cancel/', views.cancel_rental, name='cancel_rental'),
    
    # Feedback
    path('rental/<str:rental_number>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
