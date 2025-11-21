from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'books'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Books
    path('books/', views.book_list, name='book_list'),
    path('books/<slug:slug>/', views.book_detail, name='book_detail'),
    path('category/<slug:slug>/', views.category_books, name='category_books'),
    path('search/', views.search_books, name='search'),
    path('api/search/', views.live_search_api, name='live_search_api'),
    
    # Cart (Now integrated into checkout)
    path('cart/', lambda request: redirect('orders:checkout'), name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:book_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:book_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Reviews
    path('books/<slug:slug>/review/', views.add_review, name='add_review'),
]
