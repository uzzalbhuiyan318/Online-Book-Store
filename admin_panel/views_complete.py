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
from rentals.models import RentalPlan, BookRental, RentalStatusHistory, RentalSettings, RentalNotification
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
    """List all books with filtering"""
    books = Book.objects.all().select_related('category').order_by('-created_at')
    
    # Search
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)
    
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
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'categories': categories,
        'total_count': books.count(),
    }
    return render(request, 'admin_panel/book_list.html', context)


@staff_member_required
def book_add(request):
    """Add new book"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('admin_panel:book_list')
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
            book = form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('admin_panel:book_list')
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
        book_ids = request.POST.getlist('book_ids')
        
        if not book_ids:
            messages.error(request, 'No books selected!')
            return redirect('admin_panel:book_list')
        
        books = Book.objects.filter(id__in=book_ids)
        
        if action == 'activate':
            books.update(is_active=True)
            messages.success(request, f'{books.count()} books activated successfully!')
        elif action == 'deactivate':
            books.update(is_active=False)
            messages.success(request, f'{books.count()} books deactivated successfully!')
        elif action == 'delete':
            count = books.count()
            books.delete()
            messages.success(request, f'{count} books deleted successfully!')
        
        return redirect('admin_panel:book_list')
    
    return redirect('admin_panel:book_list')


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
    """List rental plans"""
    plans = RentalPlan.objects.all().order_by('order', 'days')
    
    context = {'plans': plans}
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
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'conversations': page_obj.object_list,
        'total_count': conversations.count(),
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
