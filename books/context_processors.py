"""
Context processors for books app
"""
from .models import Cart, Category, Book
from django.db.models import Count


def cart_context(request):
    """Add cart information to context"""
    cart_items = []
    cart_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).select_related('book')
    elif request.session.session_key:
        cart_items = Cart.objects.filter(session_key=request.session.session_key).select_related('book')
    
    cart_count = sum(item.quantity for item in cart_items)
    cart_total = sum(item.subtotal for item in cart_items)
    
    return {
        'cart_items': cart_items,
        'cart_count': cart_count,
        'cart_total': cart_total,
    }


def categories_context(request):
    """Add active categories, authors, and publishers to context"""
    categories = Category.objects.filter(is_active=True)
    
    # Get unique authors with book count for the site navigation (avoid clashing with
    # view-level `authors` context variables used on listing pages)
    nav_authors = Book.objects.filter(is_active=True).values('author').annotate(
        book_count=Count('id')
    ).order_by('author')[:50]  # Limit to 50 authors

    # Get unique publishers with book count for the site navigation
    nav_publishers = Book.objects.filter(is_active=True, publisher__isnull=False).exclude(
        publisher=''
    ).values('publisher').annotate(
        book_count=Count('id')
    ).order_by('publisher')[:50]  # Limit to 50 publishers
    
    return {
        'categories': categories,
        'nav_authors': nav_authors,
        'nav_publishers': nav_publishers,
    }
