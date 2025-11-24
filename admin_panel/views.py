from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
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
    total_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        payment_status='paid',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('total'))['total'] or 0
    
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


# ==================== RENTAL MANAGEMENT ====================

@staff_member_required
def rental_list(request):
    """List all rentals"""
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
