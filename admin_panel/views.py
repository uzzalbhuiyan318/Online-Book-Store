from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from books.models import Book, Category, Review, Banner, Wishlist, Cart
from orders.models import Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage, ShippingFee
from rentals.models import RentalPlan, BookRental, RentalStatusHistory, RentalSettings, RentalNotification
from support.models import SupportAgent, Conversation, Message, QuickReply, ChatSettings
from payments.models import Payment
from accounts.models import User, Address
from django.core.paginator import Paginator
from .forms import (
    BookForm, CategoryForm, OrderStatusForm, CouponForm,
    RentalPlanForm, RentalStatusForm, RentalSettingsForm,
    BannerForm, SupportAgentForm, QuickReplyForm, ChatSettingsForm,
    UserAdminForm, ReviewApprovalForm, ShippingFeeForm
)
import json
import csv


# ==================== RENTAL HELPER FUNCTIONS ====================

def get_user_rental_summary(user):
    """
    Get comprehensive rental summary for a user.
    Returns dict with active, pending, overdue counts and color coding.
    """
    settings = RentalSettings.get_settings()
    active_count = BookRental.objects.filter(user=user, status='active').count()
    pending_count = BookRental.objects.filter(user=user, status='pending').count()
    overdue_count = BookRental.objects.filter(
        user=user, status='active', due_date__lt=timezone.now()
    ).count()
    total_rentals = BookRental.objects.filter(user=user).count()
    
    # Determine color based on active rental limit
    max_rentals = settings.max_active_rentals_per_user
    if active_count >= max_rentals:
        color = 'danger'
        icon = '⚠️'
    elif active_count >= max_rentals - 1:
        color = 'warning'
        icon = '⚡'
    else:
        color = 'success'
        icon = '✓'
    
    return {
        'active_count': active_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'total_rentals': total_rentals,
        'at_limit': active_count >= max_rentals,
        'color': color,
        'icon': icon,
        'max_rentals': max_rentals
    }


def get_status_badge_html(status):
    """Generate Bootstrap badge HTML for rental status"""
    colors = {
        'pending': 'warning',
        'active': 'success',
        'returned': 'secondary',
        'overdue': 'danger',
        'cancelled': 'dark',
    }
    color = colors.get(status, 'secondary')
    return f'<span class="badge bg-{color}">{status.title()}</span>'


def get_days_info_html(rental):
    """Generate HTML for days remaining/overdue display"""
    if rental.status == 'active':
        if rental.is_overdue:
            return f'<span class="text-danger fw-bold">⚠️ Overdue by {rental.overdue_days} days</span>'
        else:
            days = rental.days_remaining
            if days <= 3:
                return f'<span class="text-warning fw-bold">⏰ {days} days remaining</span>'
            else:
                return f'<span class="text-success">{days} days remaining</span>'
    elif rental.status == 'returned':
        return '<span class="text-muted">Returned</span>'
    return '<span class="text-muted">-</span>'


# ==================== DASHBOARD & GENERAL ====================

@staff_member_required
def dashboard(request):
    """Admin Dashboard"""
    # Get date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='delivered').count()
    total_customers = User.objects.filter(is_staff=False).count()
    total_books = Book.objects.count()
    low_stock_books = Book.objects.filter(stock__lt=5, is_active=True).count()
    
    # Revenue
    # Sales Revenue (from book sales/orders)
    sales_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    monthly_sales_revenue = Order.objects.filter(
        payment_status='paid',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Rental Revenue (from book rentals)
    rental_revenue = BookRental.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_rental_revenue = BookRental.objects.filter(
        payment_status='paid',
        rental_date__gte=last_30_days
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Total Revenue (sales + rentals)
    total_revenue = sales_revenue + rental_revenue
    monthly_revenue = monthly_sales_revenue + monthly_rental_revenue
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Top selling books
    top_books = Book.objects.filter(is_active=True).order_by('-sales')[:5]
    
    # Pending reviews
    pending_reviews = Review.objects.filter(is_approved=False).count()
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_customers': total_customers,
        'total_books': total_books,
        'low_stock_books': low_stock_books,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'sales_revenue': sales_revenue,
        'monthly_sales_revenue': monthly_sales_revenue,
        'rental_revenue': rental_revenue,
        'monthly_rental_revenue': monthly_rental_revenue,
        'recent_orders': recent_orders,
        'top_books': top_books,
        'pending_reviews': pending_reviews,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def book_management(request):
    """Book Management"""
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
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'categories': categories,
    }
    return render(request, 'admin_panel/book_management.html', context)


@staff_member_required
def add_book(request):
    """Add new book"""
    if request.method == 'POST':
        # Handle book creation
        # This would use a ModelForm in production
        messages.success(request, 'Book added successfully!')
        return redirect('admin_panel:book_management')
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_panel/book_form.html', context)


@staff_member_required
def edit_book(request, pk):
    """Edit book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        # Handle book update
        messages.success(request, 'Book updated successfully!')
        return redirect('admin_panel:book_management')
    
    categories = Category.objects.all()
    context = {'book': book, 'categories': categories}
    return render(request, 'admin_panel/book_form.html', context)


@staff_member_required
def delete_book(request, pk):
    """Delete book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully!')
        return redirect('admin_panel:book_management')
    
    return render(request, 'admin_panel/book_confirm_delete.html', {'book': book})


@staff_member_required
def category_management(request):
    """Category Management"""
    categories = Category.objects.annotate(
        book_count=Count('books')
    ).order_by('order', 'name')
    
    context = {'categories': categories}
    return render(request, 'admin_panel/category_management.html', context)


@staff_member_required
def add_category(request):
    """Add new category"""
    if request.method == 'POST':
        messages.success(request, 'Category added successfully!')
        return redirect('admin_panel:category_management')
    
    return render(request, 'admin_panel/category_form.html')


@staff_member_required
def edit_category(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        messages.success(request, 'Category updated successfully!')
        return redirect('admin_panel:category_management')
    
    context = {'category': category}
    return render(request, 'admin_panel/category_form.html', context)


@staff_member_required
def delete_category(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('admin_panel:category_management')
    
    return render(request, 'admin_panel/category_confirm_delete.html', {'category': category})


@staff_member_required
def order_management(request):
    """Order Management"""
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
    }
    return render(request, 'admin_panel/order_management.html', context)


@staff_member_required
def order_detail(request, order_number):
    """Order Detail"""
    order = get_object_or_404(Order, order_number=order_number)
    order_items = OrderItem.objects.filter(order=order)
    status_history = OrderStatusHistory.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
    }
    return render(request, 'admin_panel/order_detail.html', context)


@staff_member_required
def update_order_status(request, order_number):
    """Update order status"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        tracking_number = request.POST.get('tracking_number', '')
        
        # Update order
        old_status = order.status
        order.status = new_status
        
        if tracking_number:
            order.tracking_number = tracking_number
        
        # Update timestamps
        if new_status == 'confirmed' and not order.confirmed_at:
            order.confirmed_at = timezone.now()
        elif new_status == 'shipped' and not order.shipped_at:
            order.shipped_at = timezone.now()
        elif new_status == 'delivered' and not order.delivered_at:
            order.delivered_at = timezone.now()
        
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            changed_by=request.user
        )
        
        messages.success(request, f'Order status updated to {new_status}')
        return redirect('admin_panel:order_detail', order_number=order_number)
    
    return redirect('admin_panel:order_detail', order_number=order_number)


@staff_member_required
def customer_management(request):
    """Customer Management"""
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
    }
    return render(request, 'admin_panel/customer_management.html', context)


@staff_member_required
def customer_detail(request, pk):
    """Customer Detail"""
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    orders = Order.objects.filter(user=customer).order_by('-created_at')[:10]
    
    total_orders = Order.objects.filter(user=customer).count()
    total_spent = Order.objects.filter(
        user=customer, 
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'admin_panel/customer_detail.html', context)


@staff_member_required
def review_management(request):
    """Review Management"""
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
    }
    return render(request, 'admin_panel/review_management.html', context)


@staff_member_required
def approve_review(request, pk):
    """Approve review"""
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = True
    review.save()
    messages.success(request, 'Review approved!')
    return redirect('admin_panel:review_management')


@staff_member_required
def delete_review(request, pk):
    """Delete review"""
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Review deleted!')
    return redirect('admin_panel:review_management')


# ==================== SHIPPING FEE MANAGEMENT ====================

@staff_member_required
def shipping_fee_list(request):
    """List all shipping fees"""
    from django.core.cache import cache
    
    fees = ShippingFee.objects.all().order_by('-is_default', 'city_name')
    
    # Search by city name
    query = request.GET.get('q')
    if query:
        fees = fees.filter(
            Q(city_name__icontains=query) |
            Q(city_name_bn__icontains=query)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        fees = fees.filter(is_active=True)
    elif status == 'inactive':
        fees = fees.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(fees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'fees': page_obj.object_list,
        'total_count': fees.count(),
        'active_count': ShippingFee.objects.filter(is_active=True).count(),
        'inactive_count': ShippingFee.objects.filter(is_active=False).count(),
    }
    return render(request, 'admin_panel/shipping_fee_list.html', context)


@staff_member_required
def shipping_fee_add(request):
    """Add new shipping fee"""
    from django.core.cache import cache
    
    if request.method == 'POST':
        form = ShippingFeeForm(request.POST)
        if form.is_valid():
            fee = form.save()
            # Clear cache to apply changes immediately
            cache.clear()
            messages.success(request, f'Shipping fee for "{fee.city_name}" added successfully!')
            return redirect('admin_panel:shipping_fee_list')
    else:
        form = ShippingFeeForm()
    
    context = {'form': form, 'action': 'Add'}
    return render(request, 'admin_panel/shipping_fee_form.html', context)


@staff_member_required
def shipping_fee_edit(request, pk):
    """Edit shipping fee"""
    from django.core.cache import cache
    
    fee = get_object_or_404(ShippingFee, pk=pk)
    
    if request.method == 'POST':
        form = ShippingFeeForm(request.POST, instance=fee)
        if form.is_valid():
            fee = form.save()
            # Clear cache to apply changes immediately
            cache.clear()
            messages.success(request, f'Shipping fee for "{fee.city_name}" updated successfully!')
            return redirect('admin_panel:shipping_fee_list')
    else:
        form = ShippingFeeForm(instance=fee)
    
    context = {'form': form, 'fee': fee, 'action': 'Edit'}
    return render(request, 'admin_panel/shipping_fee_form.html', context)


@staff_member_required
def shipping_fee_delete(request, pk):
    """Delete shipping fee"""
    from django.core.cache import cache
    
    fee = get_object_or_404(ShippingFee, pk=pk)
    
    if request.method == 'POST':
        city_name = fee.city_name
        fee.delete()
        # Clear cache to apply changes immediately
        cache.clear()
        messages.success(request, f'Shipping fee for "{city_name}" deleted successfully!')
        return redirect('admin_panel:shipping_fee_list')
    
    return render(request, 'admin_panel/shipping_fee_confirm_delete.html', {'fee': fee})


# ==================== RENTAL MANAGEMENT ====================

@staff_member_required
def rental_list(request):
    """List all rentals with enhanced filtering and visual indicators"""
    rentals = BookRental.objects.all().select_related('user', 'book', 'rental_plan').order_by('-created_at')

    # Search (rental number, user, book, transaction id)
    query = request.GET.get('q')
    if query:
        rentals = rentals.filter(
            Q(rental_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__full_name__icontains=query) |
            Q(book__title__icontains=query) |
            Q(transaction_id__icontains=query)
        )

    # Filter by status
    status = request.GET.get('status')
    if status:
        rentals = rentals.filter(status=status)
    
    # Filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        rentals = rentals.filter(payment_status=payment_status)

    # Filter overdue
    if request.GET.get('overdue') == '1':
        rentals = rentals.filter(status='active', due_date__lt=timezone.now())
    
    # Filter due soon (within 3 days)
    if request.GET.get('due_soon') == '1':
        three_days_from_now = timezone.now() + timedelta(days=3)
        rentals = rentals.filter(
            status='active',
            due_date__gte=timezone.now(),
            due_date__lte=three_days_from_now
        )

    # Pagination
    paginator = Paginator(rentals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add user rental summaries to each rental
    rentals_with_summaries = []
    for rental in page_obj.object_list:
        rental.user_summary = get_user_rental_summary(rental.user)
        rentals_with_summaries.append(rental)

    context = {
        'page_obj': page_obj,
        'rentals': rentals_with_summaries,
        'total_count': rentals.count(),
        'active_count': BookRental.objects.filter(status='active').count(),
        'overdue_count': BookRental.objects.filter(status='active', due_date__lt=timezone.now()).count(),
        'pending_count': BookRental.objects.filter(status='pending').count(),
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
            # mark_as_returned should handle business logic
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
        # Export selected rentals to CSV
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


# ==================== RENTAL FEEDBACK MANAGEMENT ====================

@staff_member_required
def rental_feedback_list(request):
    """List all rental feedbacks with approval management"""
    from rentals.models import RentalFeedback
    
    feedbacks = RentalFeedback.objects.all().select_related(
        'rental', 'user', 'book'
    ).order_by('-created_at')
    
    # Filter by approval status
    approval_status = request.GET.get('approval_status')
    if approval_status == 'approved':
        feedbacks = feedbacks.filter(is_approved=True)
    elif approval_status == 'pending':
        feedbacks = feedbacks.filter(is_approved=False)
    
    # Filter by rating
    rating = request.GET.get('rating')
    if rating:
        feedbacks = feedbacks.filter(overall_rating=rating)
    
    # Search
    query = request.GET.get('q')
    if query:
        feedbacks = feedbacks.filter(
            Q(rental__rental_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(book__title__icontains=query) |
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
    from rentals.models import RentalFeedback
    
    feedback = get_object_or_404(RentalFeedback, pk=pk)
    feedback.is_approved = True
    feedback.save()
    messages.success(request, 'Feedback approved successfully!')
    return redirect('admin_panel:rental_feedback_list')


@staff_member_required
def rental_feedback_delete(request, pk):
    """Delete a rental feedback"""
    from rentals.models import RentalFeedback
    
    feedback = get_object_or_404(RentalFeedback, pk=pk)
    
    if request.method == 'POST':
        feedback.delete()
        messages.success(request, 'Feedback deleted successfully!')
        return redirect('admin_panel:rental_feedback_list')
    
    context = {'feedback': feedback}
    return render(request, 'admin_panel/rental_feedback_confirm_delete.html', context)


@staff_member_required
def rental_feedback_bulk_action(request):
    """Handle bulk actions for rental feedbacks"""
    from rentals.models import RentalFeedback
    
    if request.method != 'POST':
        return redirect('admin_panel:rental_feedback_list')
    
    action = request.POST.get('action')
    selected = request.POST.getlist('selected_feedbacks')
    
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
    read_status = request.GET.get('read_status')
    if read_status == 'read':
        notifications = notifications.filter(is_read=True)
    elif read_status == 'unread':
        notifications = notifications.filter(is_read=False)
    
    # Filter by sent status
    sent_status = request.GET.get('sent_status')
    if sent_status == 'sent':
        notifications = notifications.filter(is_sent=True)
    elif sent_status == 'not_sent':
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
    selected = request.POST.getlist('selected_notifications')
    
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
    elif action == 'mark_sent':
        updated = notifications_qs.update(is_sent=True, sent_at=timezone.now())
        messages.success(request, f'{updated} notification(s) marked as sent.')
    elif action == 'delete_read':
        count = notifications_qs.filter(is_read=True).count()
        notifications_qs.filter(is_read=True).delete()
        messages.success(request, f'{count} read notification(s) deleted.')
    else:
        messages.error(request, 'Invalid action selected!')
    
    return redirect('admin_panel:rental_notification_list')


# ==================== REPORTS ====================

@staff_member_required
def sales_report(request):
    """Sales Report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.filter(payment_status='paid')
    
    if start_date:
        orders = orders.filter(created_at__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__lte=end_date)
    
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = orders.count()
    
    # Top selling books
    top_books = Book.objects.filter(is_active=True).order_by('-sales')[:10]
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'orders': orders.order_by('-created_at')[:20],
        'top_books': top_books,
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
    low_stock = Book.objects.filter(stock__lt=5, is_active=True).order_by('stock')
    
    # Out of stock
    out_of_stock = Book.objects.filter(stock=0, is_active=True)
    
    # Total inventory value
    books = Book.objects.filter(is_active=True)
    total_value = sum(book.price * book.stock for book in books)
    
    context = {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'total_value': total_value,
    }
    return render(request, 'admin_panel/inventory_report.html', context)
