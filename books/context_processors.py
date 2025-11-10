"""
Context processors for books app
"""
from .models import Cart, Category


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
    """Add active categories to context"""
    categories = Category.objects.filter(is_active=True)
    return {
        'categories': categories,
    }
