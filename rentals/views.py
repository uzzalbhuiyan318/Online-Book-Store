from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from decimal import Decimal
from .models import (
    RentalPlan, BookRental, RentalFeedback, 
    RentalNotification, RentalSettings, RentalStatusHistory
)
from books.models import Book


def rental_plans(request):
    """Display available rental plans"""
    plans = RentalPlan.objects.filter(is_active=True).order_by('order', 'days')
    
    context = {
        'plans': plans,
    }
    return render(request, 'rentals/rental_plans.html', context)


@login_required
def book_rental_detail(request, slug):
    """Book detail page with rental options"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    rental_plans = RentalPlan.objects.filter(is_active=True).order_by('order', 'days')
    settings = RentalSettings.get_settings()
    
    # Check if book is available for rental
    can_rent = book.stock >= settings.min_stock_for_rental
    
    # Check user's active rentals count
    active_rentals_count = BookRental.objects.filter(
        user=request.user,
        status='active'
    ).count()
    
    can_user_rent = active_rentals_count < settings.max_active_rentals_per_user
    
    # Calculate rental prices for each plan
    rental_prices = []
    for plan in rental_plans:
        rental_price = plan.calculate_rental_price(book.final_price)
        security_deposit = (book.final_price * settings.security_deposit_percentage) / 100
        total = rental_price + security_deposit
        
        rental_prices.append({
            'plan': plan,
            'rental_price': rental_price,
            'security_deposit': security_deposit,
            'total': total,
        })
    
    context = {
        'book': book,
        'rental_plans': rental_plans,
        'rental_prices': rental_prices,
        'can_rent': can_rent and can_user_rent,
        'max_rentals_reached': not can_user_rent,
        'active_rentals_count': active_rentals_count,
        'max_rentals': settings.max_active_rentals_per_user,
        'settings': settings,
    }
    return render(request, 'rentals/book_rental_detail.html', context)


@login_required
def create_rental(request, slug):
    """Create a new book rental"""
    if request.method == 'POST':
        book = get_object_or_404(Book, slug=slug, is_active=True)
        plan_id = request.POST.get('rental_plan')
        
        if not plan_id:
            messages.error(request, 'Please select a rental plan.')
            return redirect('rentals:book_rental_detail', slug=slug)
        
        rental_plan = get_object_or_404(RentalPlan, id=plan_id, is_active=True)
        settings = RentalSettings.get_settings()
        
        # Validate book availability
        if book.stock < settings.min_stock_for_rental:
            messages.error(request, 'This book is not available for rental at the moment.')
            return redirect('rentals:book_rental_detail', slug=slug)
        
        # Validate user rental limit
        active_rentals_count = BookRental.objects.filter(
            user=request.user,
            status='active'
        ).count()
        
        if active_rentals_count >= settings.max_active_rentals_per_user:
            messages.error(request, f'You have reached the maximum limit of {settings.max_active_rentals_per_user} active rentals.')
            return redirect('rentals:my_rentals')
        
        # Calculate prices
        rental_price = rental_plan.calculate_rental_price(book.final_price)
        security_deposit = (book.final_price * settings.security_deposit_percentage) / 100
        total_amount = rental_price + security_deposit
        
        # Create rental
        rental = BookRental.objects.create(
            user=request.user,
            book=book,
            rental_plan=rental_plan,
            rental_price=rental_price,
            security_deposit=security_deposit,
            total_amount=total_amount,
            status='pending',
            payment_status='pending',
            customer_notes=request.POST.get('notes', '')
        )
        
        # Reduce book stock
        book.stock -= 1
        book.save()
        
        # Create status history
        RentalStatusHistory.objects.create(
            rental=rental,
            status='pending',
            notes='Rental created',
            changed_by=request.user
        )
        
        # Create notification
        RentalNotification.objects.create(
            rental=rental,
            user=request.user,
            notification_type='rental_confirmed',
            title='Rental Request Received',
            message=f'Your rental request for "{book.title}" has been received. Rental Number: {rental.rental_number}'
        )
        
        messages.success(request, f'Rental request created successfully! Rental Number: {rental.rental_number}')
        return redirect('rentals:rental_detail', rental_number=rental.rental_number)
    
    return redirect('books:book_detail', slug=slug)


@login_required
def my_rentals(request):
    """List all user's rentals"""
    status_filter = request.GET.get('status', 'all')
    
    rentals = BookRental.objects.filter(user=request.user).select_related('book', 'rental_plan')
    
    if status_filter != 'all':
        rentals = rentals.filter(status=status_filter)
    
    rentals = rentals.order_by('-created_at')
    
    # Get counts for each status
    status_counts = {
        'all': BookRental.objects.filter(user=request.user).count(),
        'active': BookRental.objects.filter(user=request.user, status='active').count(),
        'pending': BookRental.objects.filter(user=request.user, status='pending').count(),
        'returned': BookRental.objects.filter(user=request.user, status='returned').count(),
        'overdue': BookRental.objects.filter(user=request.user, status='overdue').count(),
    }
    
    context = {
        'rentals': rentals,
        'status_filter': status_filter,
        'status_counts': status_counts,
    }
    return render(request, 'rentals/my_rentals.html', context)


@login_required
def rental_detail(request, rental_number):
    """View rental details"""
    rental = get_object_or_404(
        BookRental,
        rental_number=rental_number,
        user=request.user
    )
    
    # Get status history
    status_history = rental.status_history.all()
    
    # Get notifications for this rental
    notifications = rental.notifications.all()
    
    # Check if feedback exists
    has_feedback = hasattr(rental, 'feedback')
    
    context = {
        'rental': rental,
        'status_history': status_history,
        'notifications': notifications,
        'has_feedback': has_feedback,
    }
    return render(request, 'rentals/rental_detail.html', context)


@login_required
def renew_rental(request, rental_number):
    """Renew an active rental"""
    if request.method == 'POST':
        rental = get_object_or_404(
            BookRental,
            rental_number=rental_number,
            user=request.user
        )
        
        success, message = rental.renew()
        
        if success:
            # Create status history
            RentalStatusHistory.objects.create(
                rental=rental,
                status='active',
                notes=f'Rental renewed - {message}',
                changed_by=request.user
            )
            
            # Create notification
            RentalNotification.objects.create(
                rental=rental,
                user=request.user,
                notification_type='renewal_confirmed',
                title='Rental Renewed',
                message=message
            )
            
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('rentals:rental_detail', rental_number=rental_number)
    
    return redirect('rentals:my_rentals')


@login_required
def return_rental(request, rental_number):
    """Mark rental as returned"""
    if request.method == 'POST':
        rental = get_object_or_404(
            BookRental,
            rental_number=rental_number,
            user=request.user,
            status='active'
        )
        
        rental.mark_as_returned()
        
        # Create status history
        RentalStatusHistory.objects.create(
            rental=rental,
            status='returned',
            notes='Book returned by user',
            changed_by=request.user
        )
        
        # Create notification
        late_message = f' Late fee: ৳{rental.late_fee}' if rental.late_fee > 0 else ''
        RentalNotification.objects.create(
            rental=rental,
            user=request.user,
            notification_type='returned',
            title='Rental Returned',
            message=f'You have successfully returned "{rental.book.title}".{late_message}'
        )
        
        # Create feedback request notification
        RentalNotification.objects.create(
            rental=rental,
            user=request.user,
            notification_type='feedback_request',
            title='Share Your Feedback',
            message=f'Please share your experience about renting "{rental.book.title}".'
        )
        
        if rental.late_fee > 0:
            messages.warning(request, f'Book returned successfully! Late fee: ৳{rental.late_fee}')
        else:
            messages.success(request, 'Book returned successfully!')
        
        return redirect('rentals:submit_feedback', rental_number=rental_number)
    
    return redirect('rentals:rental_detail', rental_number=rental_number)


@login_required
def submit_feedback(request, rental_number):
    """Submit feedback for a returned rental"""
    rental = get_object_or_404(
        BookRental,
        rental_number=rental_number,
        user=request.user,
        status='returned'
    )
    
    # Check if feedback already exists
    if hasattr(rental, 'feedback'):
        messages.info(request, 'You have already submitted feedback for this rental.')
        return redirect('rentals:rental_detail', rental_number=rental_number)
    
    if request.method == 'POST':
        book_condition_rating = request.POST.get('book_condition_rating')
        service_rating = request.POST.get('service_rating')
        overall_rating = request.POST.get('overall_rating')
        comment = request.POST.get('comment', '')
        
        # Validate ratings
        if not all([book_condition_rating, service_rating, overall_rating]):
            messages.error(request, 'Please provide all ratings.')
            return render(request, 'rentals/submit_feedback.html', {'rental': rental})
        
        # Create feedback
        RentalFeedback.objects.create(
            rental=rental,
            user=request.user,
            book=rental.book,
            book_condition_rating=int(book_condition_rating),
            service_rating=int(service_rating),
            overall_rating=int(overall_rating),
            comment=comment
        )
        
        messages.success(request, 'Thank you for your feedback!')
        return redirect('rentals:rental_detail', rental_number=rental_number)
    
    context = {
        'rental': rental,
    }
    return render(request, 'rentals/submit_feedback.html', context)


@login_required
def notifications(request):
    """View all notifications"""
    notifications = RentalNotification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('rentals:notifications')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'rentals/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(RentalNotification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('rentals:notifications')


@login_required
def cancel_rental(request, rental_number):
    """Cancel a pending rental"""
    if request.method == 'POST':
        rental = get_object_or_404(
            BookRental,
            rental_number=rental_number,
            user=request.user,
            status='pending'
        )
        
        rental.status = 'cancelled'
        rental.save()
        
        # Return book to stock
        rental.book.stock += 1
        rental.book.save()
        
        # Create status history
        RentalStatusHistory.objects.create(
            rental=rental,
            status='cancelled',
            notes='Cancelled by user',
            changed_by=request.user
        )
        
        messages.success(request, 'Rental cancelled successfully.')
        return redirect('rentals:my_rentals')
    
    return redirect('rentals:rental_detail', rental_number=rental_number)
