# This file contains the complete admin panel views
# Copy this content to views.py after review

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime
from books.models import Book, Category, Review, Banner, Wishlist, Cart
from orders.models import Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage
from orders.models import GiftForm, GiftCity, GiftOccasion
from rentals.models import RentalPlan, BookRental, RentalStatusHistory, RentalSettings, RentalNotification, RentalFeedback
from support.models import SupportAgent, Conversation, Message, QuickReply, ChatSettings
from payments.models import Payment
from accounts.models import User, Address
from django.core.paginator import Paginator
from .forms import (
    BookForm, CategoryForm, OrderStatusForm, CouponForm,
    RentalPlanForm, RentalStatusForm, RentalSettingsForm,
    BannerForm, SupportAgentForm, QuickReplyForm, ChatSettingsForm,
    UserAdminForm, ReviewApprovalForm
)
import json
import csv


# ==================== DASHBOARD ====================

@staff_member_required
def dashboard(request):
    """Admin Dashboard with comprehensive statistics"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Order Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Revenue Statistics
    total_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        payment_status='paid',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('total'))['total'] or 0
    
    weekly_revenue = Order.objects.filter(
        payment_status='paid',
        created_at__gte=last_7_days
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Customer Statistics
    total_customers = User.objects.filter(is_staff=False).count()
    new_customers_month = User.objects.filter(
        is_staff=False,
        date_joined__gte=last_30_days
    ).count()
    
    # Product Statistics
    total_books = Book.objects.filter(is_active=True).count()
    low_stock_books = Book.objects.filter(stock__lt=5, stock__gt=0, is_active=True).count()
    out_of_stock = Book.objects.filter(stock=0, is_active=True).count()
    
    # Rental Statistics
    active_rentals = BookRental.objects.filter(status='active').count()
    overdue_rentals = BookRental.objects.filter(
        status='active',
        due_date__lt=timezone.now()
    ).count()
    
    # Support Statistics
    open_conversations = Conversation.objects.filter(status='open').count()
    pending_conversations = Conversation.objects.filter(status='pending').count()
    
    # Review Statistics
    pending_reviews = Review.objects.filter(is_approved=False).count()
    total_reviews = Review.objects.filter(is_approved=True).count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top selling books
    top_books = Book.objects.filter(is_active=True).order_by('-sales')[:5]
    
    # Low stock alert
    low_stock_items = Book.objects.filter(
        stock__lt=5, stock__gt=0, is_active=True
    ).order_by('stock')[:5]
    
    # Sales chart data (last 7 days)
    sales_data = []
    sales_labels = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_sales = Order.objects.filter(
            payment_status='paid',
            created_at__date=date
        ).aggregate(total=Sum('total'))['total'] or 0
        sales_data.append(float(daily_sales))
        sales_labels.append(date.strftime('%b %d'))
    
    # Order status data for pie chart
    order_status_data = [
        Order.objects.filter(status='pending').count(),
        Order.objects.filter(status='processing').count(),
        Order.objects.filter(status='shipped').count(),
        Order.objects.filter(status='delivered').count(),
        Order.objects.filter(status='cancelled').count(),
    ]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'weekly_revenue': weekly_revenue,
        'total_customers': total_customers,
        'new_customers_month': new_customers_month,
        'total_books': total_books,
        'low_stock_books': low_stock_books,
        'out_of_stock': out_of_stock,
        'active_rentals': active_rentals,
        'overdue_rentals': overdue_rentals,
        'open_conversations': open_conversations,
        'pending_conversations': pending_conversations,
        'pending_reviews': pending_reviews,
        'total_reviews': total_reviews,
        'recent_orders': recent_orders,
        'top_books': top_books,
        'low_stock_items': low_stock_items,
        'sales_data': json.dumps(sales_data),
        'sales_labels': json.dumps(sales_labels),
        'order_status_data': json.dumps(order_status_data),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ==================== BOOK MANAGEMENT ====================

@staff_member_required
def book_list(request):
    """List all books with filtering (matching Django admin features)"""
    books = Book.objects.all().select_related('category').order_by('-created_at')
    
    # Search (title, author, isbn, publisher)
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(publisher__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)
    
    # Filter by language
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        books = books.filter(is_active=True)
    elif status == 'inactive':
        books = books.filter(is_active=False)
    elif status == 'low_stock':
        books = books.filter(stock__lt=5, is_active=True)
    elif status == 'out_of_stock':
        books = books.filter(stock=0)
    
    # Filter by featured
    is_featured = request.GET.get('is_featured')
    if is_featured == '1':
        books = books.filter(is_featured=True)
    elif is_featured == '0':
        books = books.filter(is_featured=False)
    
    # Filter by bestseller
    is_bestseller = request.GET.get('is_bestseller')
    if is_bestseller == '1':
        books = books.filter(is_bestseller=True)
    elif is_bestseller == '0':
        books = books.filter(is_bestseller=False)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        books = books.filter(created_at__gte=date_from)
    if date_to:
        books = books.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    # Statistics
    stats = {
        'total_books': Book.objects.count(),
        'active_books': Book.objects.filter(is_active=True).count(),
        'featured_books': Book.objects.filter(is_featured=True).count(),
        'low_stock_books': Book.objects.filter(stock__lt=5, stock__gt=0).count(),
        'out_of_stock_books': Book.objects.filter(stock=0).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'categories': categories,
        'total_count': books.count(),
        'stats': stats,
        'language_choices': Book.LANGUAGE_CHOICES,
    }
    return render(request, 'admin_panel/book_list.html', context)


@staff_member_required
def book_add(request):
    """Add new book"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                book = form.save()
                # Check featured count
                if book.is_featured:
                    featured_count = Book.objects.filter(is_featured=True).count()
                    messages.success(request, f'Book "{book.title}" added successfully! (Featured books: {featured_count}/4)')
                else:
                    messages.success(request, f'Book "{book.title}" added successfully!')
                return redirect('admin_panel:book_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = BookForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/book_form.html', context)


@staff_member_required
def book_edit(request, pk):
    """Edit book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            try:
                book = form.save()
                # Check featured count
                if book.is_featured:
                    featured_count = Book.objects.filter(is_featured=True).count()
                    messages.success(request, f'Book "{book.title}" updated successfully! (Featured books: {featured_count}/4)')
                else:
                    messages.success(request, f'Book "{book.title}" updated successfully!')
                return redirect('admin_panel:book_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = BookForm(instance=book)
    
    context = {'form': form, 'book': book, 'action': 'Edit'}
    return render(request, 'admin_panel/book_form.html', context)


@staff_member_required
def book_delete(request, pk):
    """Delete book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" deleted successfully!')
        return redirect('admin_panel:book_list')
    
    return render(request, 'admin_panel/book_confirm_delete.html', {'book': book})


@staff_member_required
def book_bulk_action(request):
    """Bulk actions for books"""
    if request.method == 'POST':
        action = request.POST.get('action')
        book_ids = request.POST.getlist('selected_books')
        
        if not book_ids:
            messages.error(request, 'No books selected!')
            return redirect('admin_panel:book_list')
        
        books = Book.objects.filter(id__in=book_ids)
        count = books.count()
        
        try:
            if action == 'activate':
                books.update(is_active=True)
                messages.success(request, f'{count} books activated successfully!')
            elif action == 'deactivate':
                books.update(is_active=False)
                messages.success(request, f'{count} books deactivated successfully!')
            elif action == 'mark_featured':
                # Check featured limit
                current_featured = Book.objects.filter(is_featured=True).exclude(id__in=book_ids).count()
                if current_featured + count > 4:
                    messages.error(request, f'Cannot mark {count} books as featured. Maximum 4 books can be featured. Currently {current_featured} featured.')
                else:
                    books.update(is_featured=True)
                    messages.success(request, f'{count} books marked as featured!')
            elif action == 'unmark_featured':
                books.update(is_featured=False)
                messages.success(request, f'{count} books unmarked as featured!')
            elif action == 'mark_bestseller':
                books.update(is_bestseller=True)
                messages.success(request, f'{count} books marked as bestseller!')
            elif action == 'unmark_bestseller':
                books.update(is_bestseller=False)
                messages.success(request, f'{count} books unmarked as bestseller!')
            elif action == 'delete':
                books.delete()
                messages.success(request, f'{count} books deleted successfully!')
            else:
                messages.error(request, 'Invalid action selected!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:book_list')
    
    return redirect('admin_panel:book_list')


@staff_member_required
def book_quick_edit(request, pk):
    """Quick inline edit for book stock and status (AJAX)"""
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=pk)
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        try:
            if field == 'stock':
                book.stock = int(value)
                book.save()
                return JsonResponse({'success': True, 'message': 'Stock updated'})
            elif field == 'is_active':
                book.is_active = value == 'true'
                book.save()
                return JsonResponse({'success': True, 'message': 'Status updated'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid field'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# ==================== CATEGORY MANAGEMENT ====================

@staff_member_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(
        book_count=Count('books')
    ).order_by('order', 'name')
    
    context = {'categories': categories}
    return render(request, 'admin_panel/category_list.html', context)


@staff_member_required
def category_add(request):
    """Add new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" added successfully!')
            return redirect('admin_panel:category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/category_form.html', context)


@staff_member_required
def category_edit(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('admin_panel:category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'category': category, 'action': 'Edit'}
    return render(request, 'admin_panel/category_form.html', context)


@staff_member_required
def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('admin_panel:category_list')
    
    return render(request, 'admin_panel/category_confirm_delete.html', {'category': category})


# ==================== ORDER MANAGEMENT ====================

@staff_member_required
def order_list(request):
    """List all orders"""
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    
    # Search
    query = request.GET.get('q')
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(shipping_phone__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'total_count': orders.count(),
    }
    return render(request, 'admin_panel/order_list.html', context)


@staff_member_required
def order_detail(request, order_number):
    """Order Detail"""
    order = get_object_or_404(Order, order_number=order_number)
    order_items = OrderItem.objects.filter(order=order)
    status_history = OrderStatusHistory.objects.filter(order=order).order_by('-created_at')
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
    }
    return render(request, 'admin_panel/order_detail.html', context)


@staff_member_required
def gift_form_list(request):
    """List all submitted gift forms"""
    forms_qs = GiftForm.objects.all().select_related('order', 'city', 'area', 'zone', 'occasion').order_by('-created_at')

    status = request.GET.get('status')
    if status:
        forms_qs = forms_qs.filter(status=status)

    query = request.GET.get('q')
    if query:
        forms_qs = forms_qs.filter(
            Q(to_name__icontains=query) |
            Q(from_name__icontains=query) |
            Q(to_phone__icontains=query) |
            Q(order__order_number__icontains=query)
        )

    paginator = Paginator(forms_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'gift_forms': page_obj.object_list,
        'total_count': forms_qs.count(),
    }
    return render(request, 'admin_panel/gift_form_list.html', context)


@staff_member_required
def gift_form_detail(request, pk):
    """View / update a single gift form"""
    gift = get_object_or_404(GiftForm, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_processed':
            gift.status = 'processed'
            gift.save()
            messages.success(request, 'Gift marked as processed')
        elif action == 'mark_cancelled':
            gift.status = 'cancelled'
            gift.save()
            messages.success(request, 'Gift marked as cancelled')
        return redirect('admin_panel:gift_form_detail', pk=pk)

    context = {
        'gift': gift,
    }
    return render(request, 'admin_panel/gift_form_detail.html', context)


@staff_member_required
def gift_city_list(request):
    cities = GiftCity.objects.all().order_by('name')
    paginator = Paginator(cities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'cities': page_obj.object_list}
    return render(request, 'admin_panel/gift_city_list.html', context)


@staff_member_required
def gift_city_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            GiftCity.objects.create(name=name)
            messages.success(request, f'City "{name}" added')
            return redirect('admin_panel:gift_city_list')
        messages.error(request, 'Please provide a city name')
    return render(request, 'admin_panel/gift_city_form.html', {'action': 'Add'})


@staff_member_required
def gift_city_edit(request, pk):
    city = get_object_or_404(GiftCity, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            city.name = name
            city.save()
            messages.success(request, f'City "{name}" updated')
            return redirect('admin_panel:gift_city_list')
        messages.error(request, 'Please provide a city name')
    return render(request, 'admin_panel/gift_city_form.html', {'action': 'Edit', 'city': city})


@staff_member_required
def gift_occasion_list(request):
    occasions = GiftOccasion.objects.all().order_by('label')
    paginator = Paginator(occasions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'occasions': page_obj.object_list}
    return render(request, 'admin_panel/gift_occasion_list.html', context)


@staff_member_required
def gift_occasion_add(request):
    if request.method == 'POST':
        key = request.POST.get('key', '').strip()
        label = request.POST.get('label', '').strip()
        if key and label:
            GiftOccasion.objects.create(key=key, label=label)
            messages.success(request, f'Occasion "{label}" added')
            return redirect('admin_panel:gift_occasion_list')
        messages.error(request, 'Please provide both key and label')
    return render(request, 'admin_panel/gift_occasion_form.html', {'action': 'Add'})


@staff_member_required
def gift_occasion_edit(request, pk):
    occ = get_object_or_404(GiftOccasion, pk=pk)
    if request.method == 'POST':
        key = request.POST.get('key', '').strip()
        label = request.POST.get('label', '').strip()
        if key and label:
            occ.key = key
            occ.label = label
            occ.save()
            messages.success(request, f'Occasion "{label}" updated')
            return redirect('admin_panel:gift_occasion_list')
        messages.error(request, 'Please provide both key and label')
    return render(request, 'admin_panel/gift_occasion_form.html', {'action': 'Edit', 'occasion': occ})


@staff_member_required
def order_update_status(request, order_number):
    """Update order status"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            old_status = order.status
            order = form.save(commit=False)
            
            # Update timestamps
            if order.status == 'confirmed' and not order.confirmed_at:
                order.confirmed_at = timezone.now()
            elif order.status == 'shipped' and not order.shipped_at:
                order.shipped_at = timezone.now()
            elif order.status == 'delivered' and not order.delivered_at:
                order.delivered_at = timezone.now()
            
            order.save()
            
            # Create status history
            notes = form.cleaned_data.get('notes', '')
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                notes=notes,
                changed_by=request.user
            )
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
            return redirect('admin_panel:order_detail', order_number=order_number)
    else:
        form = OrderStatusForm(instance=order)
    
    context = {'form': form, 'order': order}
    return render(request, 'admin_panel/order_status_form.html', context)


# ==================== CUSTOMER MANAGEMENT ====================

@staff_member_required
def customer_list(request):
    """List all customers"""
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total', filter=Q(orders__payment_status='paid'))
    ).order_by('-date_joined')
    
    # Search
    query = request.GET.get('q')
    if query:
        customers = customers.filter(
            Q(email__icontains=query) |
            Q(full_name__icontains=query) |
            Q(phone__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'total_count': customers.count(),
    }
    return render(request, 'admin_panel/customer_list.html', context)


@staff_member_required
def customer_detail(request, pk):
    """Customer Detail"""
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    orders = Order.objects.filter(user=customer).order_by('-created_at')[:10]
    addresses = Address.objects.filter(user=customer)
    
    total_orders = Order.objects.filter(user=customer).count()
    total_spent = Order.objects.filter(
        user=customer, 
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'customer': customer,
        'orders': orders,
        'addresses': addresses,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'admin_panel/customer_detail.html', context)


@staff_member_required
def customer_edit(request, pk):
    """Edit customer"""
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    
    if request.method == 'POST':
        form = UserAdminForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.email}" updated successfully!')
            return redirect('admin_panel:customer_detail', pk=pk)
    else:
        form = UserAdminForm(instance=customer)
    
    context = {'form': form, 'customer': customer}
    return render(request, 'admin_panel/customer_form.html', context)


# ==================== REVIEW MANAGEMENT ====================

@staff_member_required
def review_list(request):
    """List all reviews"""
    reviews = Review.objects.all().select_related('user', 'book').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'approved':
        reviews = reviews.filter(is_approved=True)
    elif status == 'pending':
        reviews = reviews.filter(is_approved=False)
    
    # Pagination
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj.object_list,
        'total_count': reviews.count(),
    }
    return render(request, 'admin_panel/review_list.html', context)


@staff_member_required
def review_approve(request, pk):
    """Approve review"""
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = True
    review.save()
    messages.success(request, 'Review approved!')
    return redirect('admin_panel:review_list')


@staff_member_required
def review_delete(request, pk):
    """Delete review"""
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted!')
        return redirect('admin_panel:review_list')
    
    return render(request, 'admin_panel/review_confirm_delete.html', {'review': review})


@staff_member_required
def review_bulk_action(request):
    """Bulk actions for reviews"""
    if request.method == 'POST':
        action = request.POST.get('action')
        review_ids = request.POST.getlist('review_ids')
        
        if not review_ids:
            messages.error(request, 'No reviews selected!')
            return redirect('admin_panel:review_list')
        
        reviews = Review.objects.filter(id__in=review_ids)
        
        if action == 'approve':
            reviews.update(is_approved=True)
            messages.success(request, f'{reviews.count()} reviews approved!')
        elif action == 'unapprove':
            reviews.update(is_approved=False)
            messages.success(request, f'{reviews.count()} reviews unapproved!')
        elif action == 'delete':
            count = reviews.count()
            reviews.delete()
            messages.success(request, f'{count} reviews deleted!')
        
        return redirect('admin_panel:review_list')
    
    return redirect('admin_panel:review_list')


# ==================== COUPON MANAGEMENT ====================

@staff_member_required
def coupon_list(request):
    """List all coupons"""
    coupons = Coupon.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    now = timezone.now()
    if status == 'active':
        coupons = coupons.filter(is_active=True, valid_from__lte=now, valid_to__gte=now)
    elif status == 'expired':
        coupons = coupons.filter(valid_to__lt=now)
    elif status == 'upcoming':
        coupons = coupons.filter(valid_from__gt=now)
    elif status == 'inactive':
        coupons = coupons.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(coupons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'coupons': page_obj.object_list,
        'total_count': coupons.count(),
    }
    return render(request, 'admin_panel/coupon_list.html', context)


@staff_member_required
def coupon_add(request):
    """Add new coupon"""
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('admin_panel:coupon_list')
    else:
        form = CouponForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/coupon_form.html', context)


@staff_member_required
def coupon_edit(request, pk):
    """Edit coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('admin_panel:coupon_list')
    else:
        form = CouponForm(instance=coupon)
    
    context = {'form': form, 'coupon': coupon, 'action': 'Edit'}
    return render(request, 'admin_panel/coupon_form.html', context)


@staff_member_required
def coupon_delete(request, pk):
    """Delete coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon "{code}" deleted successfully!')
        return redirect('admin_panel:coupon_list')
    
    return render(request, 'admin_panel/coupon_confirm_delete.html', {'coupon': coupon})


# ==================== RENTAL MANAGEMENT ====================

@staff_member_required
def rental_list(request):
    """List all rentals"""
    rentals = BookRental.objects.all().select_related('user', 'book', 'rental_plan').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        rentals = rentals.filter(status=status)
    
    # Filter overdue
    if request.GET.get('overdue') == '1':
        rentals = rentals.filter(status='active', due_date__lt=timezone.now())
    
    # Pagination
    paginator = Paginator(rentals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'rentals': page_obj.object_list,
        'total_count': rentals.count(),
    }
    return render(request, 'admin_panel/rental_list.html', context)


@staff_member_required
def rental_bulk_action(request):
    """Handle bulk actions for rentals (activate, return, cancel, calculate fees, send reminders, export)"""
    if request.method != 'POST':
        return redirect('admin_panel:rental_list')

    action = request.POST.get('action')
    selected = request.POST.getlist('selected_rentals')
    if not selected:
        messages.error(request, 'No rentals selected!')
        return redirect('admin_panel:rental_list')

    rentals_qs = BookRental.objects.filter(id__in=selected)

    if action == 'activate':
        updated = rentals_qs.filter(status='pending').update(status='active', start_date=timezone.now())
        messages.success(request, f'{updated} rental(s) marked as active.')
    elif action == 'return':
        count = 0
        for r in rentals_qs.filter(status='active'):
            if hasattr(r, 'mark_as_returned'):
                r.mark_as_returned()
            else:
                r.status = 'returned'
                r.return_date = timezone.now()
                r.save()
            count += 1
        messages.success(request, f'{count} rental(s) marked as returned.')
    elif action == 'cancel':
        updated = rentals_qs.filter(status__in=['pending', 'active']).update(status='cancelled')
        messages.success(request, f'{updated} rental(s) cancelled.')
    elif action == 'calculate_late_fees':
        count = 0
        total_fee = 0
        settings = RentalSettings.get_settings()
        for r in rentals_qs.filter(status='active'):
            if getattr(r, 'is_overdue', False):
                fee = r.calculate_late_fee(settings.daily_late_fee)
                total_fee += fee
                count += 1
        messages.success(request, f'Calculated late fees for {count} rental(s). Total: ৳{total_fee}')
    elif action == 'send_due_reminder':
        count = 0
        for r in rentals_qs.filter(status='active'):
            if getattr(r, 'days_remaining', 0) <= 3 and getattr(r, 'days_remaining', 0) > 0:
                RentalNotification.objects.create(
                    rental=r,
                    user=r.user,
                    notification_type='due_soon',
                    title=f'Reminder: Book Due in {r.days_remaining} Days',
                    message=f'Your rental for "{r.book.title}" is due on {r.due_date.strftime("%d %b, %Y")}. Please return or renew it soon.'
                )
                count += 1
        messages.success(request, f'Sent due date reminders for {count} rental(s).')
    elif action == 'send_overdue_notice':
        count = 0
        settings = RentalSettings.get_settings()
        for r in rentals_qs.filter(status='active'):
            if getattr(r, 'is_overdue', False):
                late_fee = r.calculate_late_fee(settings.daily_late_fee)
                RentalNotification.objects.create(
                    rental=r,
                    user=r.user,
                    notification_type='overdue',
                    title=f'⚠️ Book Overdue - Action Required',
                    message=f'Your rental for "{r.book.title}" is {r.overdue_days} day(s) overdue. Late fee: ৳{late_fee}. Please return the book immediately.'
                )
                count += 1
        messages.success(request, f'Sent overdue notices for {count} rental(s).')
    elif action == 'export':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rentals_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Rental Number','User','Email','Book','Plan','Status','Start Date','Due Date','Amount','Created At'])
        for r in rentals_qs.order_by('-created_at'):
            writer.writerow([
                getattr(r, 'rental_number', ''),
                r.user.full_name or '',
                r.user.email,
                getattr(r.book, 'title', ''),
                getattr(getattr(r, 'rental_plan', None), 'name', ''),
                r.get_status_display(),
                r.start_date.strftime('%Y-%m-%d') if r.start_date else '',
                r.due_date.strftime('%Y-%m-%d') if r.due_date else '',
                getattr(r, 'total_amount', getattr(r, 'amount', '')),
                r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
            ])
        return response
    else:
        messages.error(request, 'Invalid action selected!')

    return redirect('admin_panel:rental_list')


@staff_member_required
def rental_detail(request, rental_number):
    """Rental Detail"""
    rental = get_object_or_404(BookRental, rental_number=rental_number)
    status_history = RentalStatusHistory.objects.filter(rental=rental).order_by('-created_at')
    
    context = {
        'rental': rental,
        'status_history': status_history,
    }
    return render(request, 'admin_panel/rental_detail.html', context)


@staff_member_required
def rental_update_status(request, rental_number):
    """Update rental status"""
    rental = get_object_or_404(BookRental, rental_number=rental_number)
    
    if request.method == 'POST':
        form = RentalStatusForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save(commit=False)
            
            if rental.status == 'returned' and not rental.return_date:
                rental.return_date = timezone.now()
            
            rental.save()
            
            # Create status history
            notes = form.cleaned_data.get('notes', '')
            RentalStatusHistory.objects.create(
                rental=rental,
                status=rental.status,
                notes=notes,
                changed_by=request.user
            )
            
            messages.success(request, f'Rental status updated to {rental.get_status_display()}')
            return redirect('admin_panel:rental_detail', rental_number=rental_number)
    else:
        form = RentalStatusForm(instance=rental)
    
    context = {'form': form, 'rental': rental}
    return render(request, 'admin_panel/rental_status_form.html', context)


@staff_member_required
def rental_plan_list(request):
    """List rental plans with enhanced management features"""
    plans = RentalPlan.objects.all().order_by('order', 'days')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        plans = plans.filter(is_active=True)
    elif status == 'inactive':
        plans = plans.filter(is_active=False)
    
    # Search
    query = request.GET.get('q')
    if query:
        plans = plans.filter(name__icontains=query)
    
    # Pagination
    paginator = Paginator(plans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'plans': page_obj.object_list,
        'total_count': RentalPlan.objects.count(),
        'active_count': RentalPlan.objects.filter(is_active=True).count(),
        'inactive_count': RentalPlan.objects.filter(is_active=False).count(),
    }
    return render(request, 'admin_panel/rental_plan_list.html', context)


@staff_member_required
def rental_plan_add(request):
    """Add rental plan"""
    if request.method == 'POST':
        form = RentalPlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Rental plan "{plan.name}" created successfully!')
            return redirect('admin_panel:rental_plan_list')
    else:
        form = RentalPlanForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/rental_plan_form.html', context)


@staff_member_required
def rental_plan_edit(request, pk):
    """Edit rental plan"""
    plan = get_object_or_404(RentalPlan, pk=pk)
    
    if request.method == 'POST':
        form = RentalPlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Rental plan "{plan.name}" updated successfully!')
            return redirect('admin_panel:rental_plan_list')
    else:
        form = RentalPlanForm(instance=plan)
    
    context = {'form': form, 'plan': plan, 'action': 'Edit'}
    return render(request, 'admin_panel/rental_plan_form.html', context)


@staff_member_required
def rental_plan_delete(request, pk):
    """Delete rental plan"""
    plan = get_object_or_404(RentalPlan, pk=pk)
    
    if request.method == 'POST':
        name = plan.name
        plan.delete()
        messages.success(request, f'Rental plan "{name}" deleted successfully!')
        return redirect('admin_panel:rental_plan_list')
    
    return render(request, 'admin_panel/rental_plan_confirm_delete.html', {'plan': plan})


@staff_member_required
def rental_plan_bulk_action(request):
    """Handle bulk actions for rental plans"""
    if request.method != 'POST':
        return redirect('admin_panel:rental_plan_list')
    
    action = request.POST.get('action')
    selected = request.POST.getlist('plan_ids')
    
    if not selected:
        messages.error(request, 'No plans selected!')
        return redirect('admin_panel:rental_plan_list')
    
    plans_qs = RentalPlan.objects.filter(id__in=selected)
    
    if action == 'activate':
        updated = plans_qs.update(is_active=True)
        messages.success(request, f'{updated} plan(s) activated.')
    elif action == 'deactivate':
        updated = plans_qs.update(is_active=False)
        messages.success(request, f'{updated} plan(s) deactivated.')
    elif action == 'delete':
        count = plans_qs.count()
        plans_qs.delete()
        messages.success(request, f'{count} plan(s) deleted.')
    else:
        messages.error(request, 'Invalid action selected!')
    
    return redirect('admin_panel:rental_plan_list')


@staff_member_required
def rental_plan_toggle_status(request, pk):
    """Toggle rental plan active status"""
    plan = get_object_or_404(RentalPlan, pk=pk)
    plan.is_active = not plan.is_active
    plan.save()
    
    status = "activated" if plan.is_active else "deactivated"
    messages.success(request, f'Plan "{plan.name}" {status}.')
    return redirect('admin_panel:rental_plan_list')


@staff_member_required
def rental_settings(request):
    """Rental settings"""
    settings_obj, created = RentalSettings.objects.get_or_create()
    
    if request.method == 'POST':
        form = RentalSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rental settings updated successfully!')
            return redirect('admin_panel:rental_settings')
    else:
        form = RentalSettingsForm(instance=settings_obj)
    
    context = {'form': form, 'settings': settings_obj}
    return render(request, 'admin_panel/rental_settings.html', context)


# ==================== BANNER MANAGEMENT ====================

@staff_member_required
def banner_list(request):
    """List all banners"""
    banners = Banner.objects.all().order_by('order', '-created_at')
    
    context = {'banners': banners}
    return render(request, 'admin_panel/banner_list.html', context)


@staff_member_required
def banner_add(request):
    """Add new banner"""
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner.title}" added successfully!')
            return redirect('admin_panel:banner_list')
    else:
        form = BannerForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/banner_form.html', context)


@staff_member_required
def banner_edit(request, pk):
    """Edit banner"""
    banner = get_object_or_404(Banner, pk=pk)
    
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner.title}" updated successfully!')
            return redirect('admin_panel:banner_list')
    else:
        form = BannerForm(instance=banner)
    
    context = {'form': form, 'banner': banner, 'action': 'Edit'}
    return render(request, 'admin_panel/banner_form.html', context)


@staff_member_required
def banner_delete(request, pk):
    """Delete banner"""
    banner = get_object_or_404(Banner, pk=pk)
    
    if request.method == 'POST':
        title = banner.title
        banner.delete()
        messages.success(request, f'Banner "{title}" deleted successfully!')
        return redirect('admin_panel:banner_list')
    
    return render(request, 'admin_panel/banner_confirm_delete.html', {'banner': banner})


# ==================== SUPPORT MANAGEMENT ====================

@staff_member_required
def support_conversation_list(request):
    """List all support conversations"""
    conversations = Conversation.objects.all().select_related('user', 'assigned_agent').order_by('-last_message_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        conversations = conversations.filter(status=status)
    
    # Filter by conversion
    converted = request.GET.get('converted')
    if converted == '1':
        conversations = conversations.filter(is_converted=True)
    elif converted == '0':
        conversations = conversations.filter(is_converted=False)
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Conversion stats
    total_conversations = Conversation.objects.count()
    converted_conversations = Conversation.objects.filter(is_converted=True).count()
    conversion_rate = (converted_conversations / total_conversations * 100) if total_conversations > 0 else 0
    
    context = {
        'page_obj': page_obj,
        'conversations': page_obj.object_list,
        'total_count': conversations.count(),
        'total_conversations': total_conversations,
        'converted_conversations': converted_conversations,
        'conversion_rate': round(conversion_rate, 2),
    }
    return render(request, 'admin_panel/support_conversation_list.html', context)


@staff_member_required
def support_agent_list(request):
    """List all support agents"""
    agents = SupportAgent.objects.all().select_related('user').order_by('order')
    
    context = {'agents': agents}
    return render(request, 'admin_panel/support_agent_list.html', context)


@staff_member_required
def support_agent_add(request):
    """Add support agent"""
    if request.method == 'POST':
        form = SupportAgentForm(request.POST, request.FILES)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f'Support agent "{agent.display_name}" added successfully!')
            return redirect('admin_panel:support_agent_list')
    else:
        form = SupportAgentForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/support_agent_form.html', context)


@staff_member_required
def support_agent_edit(request, pk):
    """Edit support agent"""
    agent = get_object_or_404(SupportAgent, pk=pk)
    
    if request.method == 'POST':
        form = SupportAgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f'Support agent "{agent.display_name}" updated successfully!')
            return redirect('admin_panel:support_agent_list')
    else:
        form = SupportAgentForm(instance=agent)
    
    context = {'form': form, 'agent': agent, 'action': 'Edit'}
    return render(request, 'admin_panel/support_agent_form.html', context)


@staff_member_required
def support_conversation_detail(request, conversation_id):
    """View conversation details with conversion tracking"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    messages_list = Message.objects.filter(conversation=conversation).select_related('sender').order_by('created_at')
    
    # Get related orders from the user
    from orders.models import Order
    user_orders = Order.objects.filter(user=conversation.user).order_by('-created_at')[:5]
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'user_orders': user_orders,
    }
    return render(request, 'admin_panel/support_conversation_detail.html', context)


@staff_member_required
def support_conversation_toggle_conversion(request, conversation_id):
    """Toggle conversation conversion status"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    if request.method == 'POST':
        conversation.is_converted = not conversation.is_converted
        notes = request.POST.get('notes', '').strip()
        if notes:
            conversation.conversion_notes = notes
        conversation.save()
        
        status_text = "marked as converted" if conversation.is_converted else "unmarked as converted"
        messages.success(request, f'Conversation {status_text} successfully!')
        
        # Return to the referring page or conversation list
        return redirect(request.META.get('HTTP_REFERER', 'admin_panel:support_conversation_list'))
    
    return redirect('admin_panel:support_conversation_list')


@staff_member_required
def support_conversion_report(request):
    """Support conversion report showing agent performance"""
    # Get date range
    from datetime import datetime
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    conversations = Conversation.objects.all()
    
    if start_date:
        conversations = conversations.filter(created_at__date__gte=start_date)
    if end_date:
        conversations = conversations.filter(created_at__date__lte=end_date)
    
    # Overall stats
    total_conversations = conversations.count()
    converted_conversations = conversations.filter(is_converted=True).count()
    conversion_rate = (converted_conversations / total_conversations * 100) if total_conversations > 0 else 0
    
    # Agent performance
    agents = SupportAgent.objects.all()
    agent_stats = []
    
    for agent in agents:
        agent_convs = conversations.filter(assigned_agent=agent)
        agent_total = agent_convs.count()
        agent_converted = agent_convs.filter(is_converted=True).count()
        agent_rate = (agent_converted / agent_total * 100) if agent_total > 0 else 0
        
        agent_stats.append({
            'agent': agent,
            'total_conversations': agent_total,
            'converted_conversations': agent_converted,
            'conversion_rate': round(agent_rate, 2),
        })
    
    # Sort by conversion rate
    agent_stats.sort(key=lambda x: x['conversion_rate'], reverse=True)
    
    context = {
        'total_conversations': total_conversations,
        'converted_conversations': converted_conversations,
        'conversion_rate': round(conversion_rate, 2),
        'agent_stats': agent_stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/support_conversion_report.html', context)


@staff_member_required
def quick_reply_list(request):
    """List quick replies"""
    replies = QuickReply.objects.all().order_by('category', 'order')
    
    context = {'replies': replies}
    return render(request, 'admin_panel/quick_reply_list.html', context)


@staff_member_required
def quick_reply_add(request):
    """Add quick reply"""
    if request.method == 'POST':
        form = QuickReplyForm(request.POST)
        if form.is_valid():
            reply = form.save()
            messages.success(request, f'Quick reply "{reply.title}" added successfully!')
            return redirect('admin_panel:quick_reply_list')
    else:
        form = QuickReplyForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/quick_reply_form.html', context)


@staff_member_required
def quick_reply_edit(request, pk):
    """Edit quick reply"""
    reply = get_object_or_404(QuickReply, pk=pk)
    
    if request.method == 'POST':
        form = QuickReplyForm(request.POST, instance=reply)
        if form.is_valid():
            reply = form.save()
            messages.success(request, f'Quick reply "{reply.title}" updated successfully!')
            return redirect('admin_panel:quick_reply_list')
    else:
        form = QuickReplyForm(instance=reply)
    
    context = {'form': form, 'reply': reply, 'action': 'Edit'}
    return render(request, 'admin_panel/quick_reply_form.html', context)


@staff_member_required
def chat_settings(request):
    """Chat settings"""
    settings_obj, created = ChatSettings.objects.get_or_create()
    
    if request.method == 'POST':
        form = ChatSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chat settings updated successfully!')
            return redirect('admin_panel:chat_settings')
    else:
        form = ChatSettingsForm(instance=settings_obj)
    
    context = {'form': form, 'settings': settings_obj}
    return render(request, 'admin_panel/chat_settings.html', context)


# ==================== REPORTS ====================

@staff_member_required
def sales_report(request):
    """Sales Report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.filter(payment_status='paid')
    
    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)
    
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = orders.count()
    average_order = total_sales / total_orders if total_orders > 0 else 0
    
    # Top selling books
    top_books = Book.objects.filter(is_active=True).order_by('-sales')[:10]
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order': average_order,
        'orders': orders.order_by('-created_at')[:20],
        'top_books': top_books,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/sales_report.html', context)


@staff_member_required
def customer_report(request):
    """Customer Report"""
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total', filter=Q(orders__payment_status='paid'))
    ).order_by('-total_spent')[:20]
    
    context = {'customers': customers}
    return render(request, 'admin_panel/customer_report.html', context)


@staff_member_required
def inventory_report(request):
    """Inventory Report"""
    # Low stock books
    low_stock = Book.objects.filter(stock__lt=5, stock__gt=0, is_active=True).order_by('stock')
    
    # Out of stock
    out_of_stock = Book.objects.filter(stock=0, is_active=True)
    
    # Total inventory value
    books = Book.objects.filter(is_active=True)
    total_value = sum(float(book.price) * book.stock for book in books)
    total_books = books.aggregate(total=Sum('stock'))['total'] or 0
    
    context = {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'total_value': total_value,
        'total_books': total_books,
    }
    return render(request, 'admin_panel/inventory_report.html', context)


# ==================== EXPORT FUNCTIONS ====================

@staff_member_required
def export_orders_csv(request):
    """Export orders to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order Number', 'Customer', 'Email', 'Status', 'Payment Status', 'Total', 'Created At'])
    
    orders = Order.objects.all().select_related('user')
    for order in orders:
        writer.writerow([
            order.order_number,
            order.user.full_name,
            order.user.email,
            order.get_status_display(),
            order.get_payment_status_display(),
            order.total,
            order.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@staff_member_required
def export_customers_csv(request):
    """Export customers to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Full Name', 'Phone', 'Date Joined', 'Active'])
    
    customers = User.objects.filter(is_staff=False)
    for customer in customers:
        writer.writerow([
            customer.email,
            customer.full_name,
            customer.phone or '',
            customer.date_joined.strftime('%Y-%m-%d'),
            'Yes' if customer.is_active else 'No'
        ])
    
    return response


@staff_member_required
def export_books_csv(request):
    """Export books to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Author', 'Category', 'Price', 'Stock', 'Sales', 'Active'])
    
    books = Book.objects.all().select_related('category')
    for book in books:
        writer.writerow([
            book.title,
            book.author,
            book.category.name if book.category else '',
            book.price,
            book.stock,
            book.sales,
            'Yes' if book.is_active else 'No'
        ])
    
    return response


# ==================== RENTAL FEEDBACK MANAGEMENT ====================

@staff_member_required
def rental_feedback_list(request):
    """List all rental feedbacks with approval management"""
    feedbacks = RentalFeedback.objects.all().select_related(
        'rental__user', 'rental__book'
    ).order_by('-created_at')
    
    # Filter by approval status
    is_approved = request.GET.get('is_approved')
    if is_approved == '1':
        feedbacks = feedbacks.filter(is_approved=True)
    elif is_approved == '0':
        feedbacks = feedbacks.filter(is_approved=False)
    
    # Filter by rating
    rating = request.GET.get('rating')
    if rating:
        feedbacks = feedbacks.filter(rating=rating)
    
    # Search
    query = request.GET.get('q')
    if query:
        feedbacks = feedbacks.filter(
            Q(rental__rental_number__icontains=query) |
            Q(rental__user__email__icontains=query) |
            Q(rental__book__title__icontains=query) |
            Q(comment__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(feedbacks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'feedbacks': page_obj.object_list,
        'total_count': feedbacks.count(),
        'approved_count': RentalFeedback.objects.filter(is_approved=True).count(),
        'pending_count': RentalFeedback.objects.filter(is_approved=False).count(),
    }
    return render(request, 'admin_panel/rental_feedback_list.html', context)


@staff_member_required
def rental_feedback_approve(request, pk):
    """Approve a rental feedback"""
    feedback = get_object_or_404(RentalFeedback, pk=pk)
    feedback.is_approved = True
    feedback.save()
    messages.success(request, 'Feedback approved successfully!')
    return redirect('admin_panel:rental_feedback_list')


@staff_member_required
def rental_feedback_delete(request, pk):
    """Delete a rental feedback"""
    feedback = get_object_or_404(RentalFeedback, pk=pk)
    feedback.delete()
    messages.success(request, 'Feedback deleted successfully!')
    return redirect('admin_panel:rental_feedback_list')


@staff_member_required
def rental_feedback_bulk_action(request):
    """Handle bulk actions for rental feedbacks"""
    if request.method != 'POST':
        return redirect('admin_panel:rental_feedback_list')
    
    action = request.POST.get('action')
    selected = request.POST.getlist('feedback_ids')
    
    if not selected:
        messages.error(request, 'No feedbacks selected!')
        return redirect('admin_panel:rental_feedback_list')
    
    feedbacks_qs = RentalFeedback.objects.filter(id__in=selected)
    
    if action == 'approve':
        updated = feedbacks_qs.update(is_approved=True)
        messages.success(request, f'{updated} feedback(s) approved.')
    elif action == 'unapprove':
        updated = feedbacks_qs.update(is_approved=False)
        messages.success(request, f'{updated} feedback(s) unapproved.')
    elif action == 'delete':
        count = feedbacks_qs.count()
        feedbacks_qs.delete()
        messages.success(request, f'{count} feedback(s) deleted.')
    else:
        messages.error(request, 'Invalid action selected!')
    
    return redirect('admin_panel:rental_feedback_list')


# ==================== RENTAL NOTIFICATION MANAGEMENT ====================

@staff_member_required
def rental_notification_list(request):
    """List all rental notifications"""
    notifications = RentalNotification.objects.all().select_related(
        'user', 'rental'
    ).order_by('-created_at')
    
    # Filter by notification type
    notif_type = request.GET.get('notification_type')
    if notif_type:
        notifications = notifications.filter(notification_type=notif_type)
    
    # Filter by read status
    is_read = request.GET.get('is_read')
    if is_read == '1':
        notifications = notifications.filter(is_read=True)
    elif is_read == '0':
        notifications = notifications.filter(is_read=False)
    
    # Filter by sent status
    is_sent = request.GET.get('is_sent')
    if is_sent == '1':
        notifications = notifications.filter(is_sent=True)
    elif is_sent == '0':
        notifications = notifications.filter(is_sent=False)
    
    # Search
    query = request.GET.get('q')
    if query:
        notifications = notifications.filter(
            Q(user__email__icontains=query) |
            Q(user__full_name__icontains=query) |
            Q(title__icontains=query) |
            Q(message__icontains=query) |
            Q(rental__rental_number__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'total_count': notifications.count(),
        'unread_count': RentalNotification.objects.filter(is_read=False).count(),
        'sent_count': RentalNotification.objects.filter(is_sent=True).count(),
    }
    return render(request, 'admin_panel/rental_notification_list.html', context)


@staff_member_required
def rental_notification_bulk_action(request):
    """Handle bulk actions for rental notifications"""
    if request.method != 'POST':
        return redirect('admin_panel:rental_notification_list')
    
    action = request.POST.get('action')
    selected = request.POST.getlist('notification_ids')
    
    if not selected:
        messages.error(request, 'No notifications selected!')
        return redirect('admin_panel:rental_notification_list')
    
    notifications_qs = RentalNotification.objects.filter(id__in=selected)
    
    if action == 'mark_read':
        updated = notifications_qs.update(is_read=True)
        messages.success(request, f'{updated} notification(s) marked as read.')
    elif action == 'mark_unread':
        updated = notifications_qs.update(is_read=False)
        messages.success(request, f'{updated} notification(s) marked as unread.')
    elif action == 'delete':
        count = notifications_qs.count()
        notifications_qs.delete()
        messages.success(request, f'{count} notification(s) deleted.')
    else:
        messages.error(request, 'Invalid action selected!')
    
    return redirect('admin_panel:rental_notification_list')
