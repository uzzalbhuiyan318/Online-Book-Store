from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Book, Category, Cart, Wishlist, Review, Banner
from .forms import ReviewForm


def home(request):
    """Homepage view"""
    banners = Banner.objects.filter(is_active=True).order_by('order')[:5]
    featured_books = Book.objects.filter(is_active=True, is_featured=True)[:8]
    bestsellers = Book.objects.filter(is_active=True, is_bestseller=True)[:8]
    new_arrivals = Book.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    # Get user's wishlist book IDs for authenticated users
    wishlist_book_ids = []
    if request.user.is_authenticated:
        wishlist_book_ids = list(Wishlist.objects.filter(user=request.user).values_list('book_id', flat=True))
    
    context = {
        'banners': banners,
        'featured_books': featured_books,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'wishlist_book_ids': wishlist_book_ids,
    }
    return render(request, 'books/home.html', context)


def book_list(request):
    """Book listing with filters"""
    books = Book.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        books = books.filter(category__slug=category_slug)
    
    # Filter by language
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)
    
    # Filter by author
    author = request.GET.get('author')
    if author:
        books = books.filter(author=author)
    
    # Filter by publisher
    publisher = request.GET.get('publisher')
    if publisher:
        books = books.filter(publisher=publisher)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        books = books.filter(price__gte=min_price)
    if max_price:
        books = books.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_low':
        books = books.order_by('price')
    elif sort_by == 'price_high':
        books = books.order_by('-price')
    elif sort_by == 'title':
        books = books.order_by('title')
    elif sort_by == 'popular':
        books = books.order_by('-views', '-sales')
    else:
        books = books.order_by('-created_at')
    
    # Get unique authors and publishers for filter dropdowns
    authors = Book.objects.filter(is_active=True).values_list('author', flat=True).distinct().order_by('author')
    publishers = Book.objects.filter(is_active=True, publisher__isnull=False).exclude(publisher='').values_list('publisher', flat=True).distinct().order_by('publisher')
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get wishlist book IDs for authenticated users
    wishlist_book_ids = []
    if request.user.is_authenticated:
        wishlist_book_ids = list(Wishlist.objects.filter(user=request.user).values_list('book_id', flat=True))
    
    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'wishlist_book_ids': wishlist_book_ids,
        'authors': authors,
        'publishers': publishers,
    }
    return render(request, 'books/book_list.html', context)


def category_books(request, slug):
    """Books by category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    books = Book.objects.filter(is_active=True, category=category)
    
    # Filter by language
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)
    
    # Filter by author
    author = request.GET.get('author')
    if author:
        books = books.filter(author=author)
    
    # Filter by publisher
    publisher = request.GET.get('publisher')
    if publisher:
        books = books.filter(publisher=publisher)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        books = books.filter(price__gte=min_price)
    if max_price:
        books = books.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_low':
        books = books.order_by('price')
    elif sort_by == 'price_high':
        books = books.order_by('-price')
    elif sort_by == 'title':
        books = books.order_by('title')
    else:
        books = books.order_by('-created_at')
    
    # Get unique authors and publishers for filter dropdowns (from this category only)
    authors = Book.objects.filter(is_active=True, category=category).values_list('author', flat=True).distinct().order_by('author')
    publishers = Book.objects.filter(is_active=True, category=category, publisher__isnull=False).exclude(publisher='').values_list('publisher', flat=True).distinct().order_by('publisher')
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get wishlist book IDs for authenticated users
    wishlist_book_ids = []
    if request.user.is_authenticated:
        wishlist_book_ids = list(Wishlist.objects.filter(user=request.user).values_list('book_id', flat=True))
    
    # Get all categories for the category filter dropdown
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'wishlist_book_ids': wishlist_book_ids,
        'authors': authors,
        'publishers': publishers,
        'categories': categories,
    }
    return render(request, 'books/category_books.html', context)


def book_detail(request, slug):
    """Book detail view"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    # Increment views
    book.views += 1
    book.save(update_fields=['views'])
    
    # Get reviews
    reviews = Review.objects.filter(book=book, is_approved=True).select_related('user')
    
    # Check if user already reviewed
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(book=book, user=request.user).exists()
    
    # Related books
    related_books = Book.objects.filter(
        category=book.category, 
        is_active=True
    ).exclude(id=book.id)[:4]
    
    context = {
        'book': book,
        'reviews': reviews,
        'user_has_reviewed': user_has_reviewed,
        'related_books': related_books,
    }
    return render(request, 'books/book_detail.html', context)


def search_books(request):
    """Search books"""
    query = request.GET.get('q', '')
    books = Book.objects.filter(is_active=True)
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(publisher__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'books': page_obj.object_list,
    }
    return render(request, 'books/search_results.html', context)


def cart(request):
    """Shopping cart view"""
    cart_items = []
    
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).select_related('book')
    elif request.session.session_key:
        cart_items = Cart.objects.filter(session_key=request.session.session_key).select_related('book')
    
    subtotal = sum(item.subtotal for item in cart_items)
    shipping = 60 if subtotal > 0 else 0  # Flat shipping rate
    total = subtotal + shipping
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    }
    return render(request, 'books/cart.html', context)


def add_to_cart(request, book_id):
    """Add book to cart"""
    book = get_object_or_404(Book, id=book_id, is_active=True)
    
    if not book.is_in_stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'This book is out of stock.'})
        messages.error(request, 'This book is out of stock.')
        return redirect('books:book_detail', slug=book.slug)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            book=book,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Get cart count for authenticated users
        cart_count = Cart.objects.filter(user=request.user).count()
    else:
        if not request.session.session_key:
            request.session.create()
        
        cart_item, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            book=book,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Get cart count for guest users
        cart_count = Cart.objects.filter(session_key=request.session.session_key).count()
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{book.title} added to cart!',
            'cart_count': cart_count
        })
    
    messages.success(request, f'{book.title} added to cart!')
    return redirect('books:cart')


def update_cart(request, cart_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if request.user.is_authenticated:
            cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        else:
            cart_item = get_object_or_404(Cart, id=cart_id, session_key=request.session.session_key)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    
    return redirect('books:cart')


def remove_from_cart(request, cart_id):
    """Remove item from cart"""
    if request.user.is_authenticated:
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    else:
        cart_item = get_object_or_404(Cart, id=cart_id, session_key=request.session.session_key)
    
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('books:cart')


def clear_cart(request):
    """Clear all items from cart"""
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    elif request.session.session_key:
        Cart.objects.filter(session_key=request.session.session_key).delete()
    
    messages.success(request, 'Cart cleared!')
    return redirect('books:cart')


@login_required
def wishlist(request):
    """User wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('book')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'books/wishlist.html', context)


@login_required
def add_to_wishlist(request, book_id):
    """Add book to wishlist"""
    book = get_object_or_404(Book, id=book_id, is_active=True)
    
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, book=book)
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if created:
            return JsonResponse({
                'success': True,
                'message': f'{book.title} added to wishlist!',
                'in_wishlist': True
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'This book is already in your wishlist.',
                'in_wishlist': True
            })
    
    # Regular form submission
    if created:
        messages.success(request, f'{book.title} added to wishlist!')
    else:
        messages.info(request, 'This book is already in your wishlist.')
    
    return redirect('books:book_detail', slug=book.slug)


@login_required
def remove_from_wishlist(request, book_id):
    """Remove book from wishlist"""
    wishlist_item = get_object_or_404(Wishlist, user=request.user, book_id=book_id)
    book_title = wishlist_item.book.title
    wishlist_item.delete()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{book_title} removed from wishlist!',
            'in_wishlist': False
        })
    
    # Regular form submission
    messages.success(request, 'Item removed from wishlist!')
    return redirect('books:wishlist')


@login_required
def add_review(request, slug):
    """Add book review"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    # Check if user already reviewed
    if Review.objects.filter(book=book, user=request.user).exists():
        messages.error(request, 'You have already reviewed this book.')
        return redirect('books:book_detail', slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you for your review! It will be visible after approval.')
            return redirect('books:book_detail', slug=slug)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'book': book,
    }
    return render(request, 'books/add_review.html', context)
