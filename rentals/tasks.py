"""
Celery tasks for rental notifications and late fee calculations
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_due_soon_rentals():
    """
    Check for rentals that are due soon and send reminder emails
    Runs daily to check rentals due in 3 days, 2 days, 1 day
    """
    from .models import BookRental, RentalSettings, RentalNotification
    from .email_utils import send_rental_due_soon_email
    
    settings = RentalSettings.get_settings()
    
    if not settings.enable_notifications:
        logger.info("Rental notifications are disabled")
        return
    
    # Get active rentals
    active_rentals = BookRental.objects.filter(
        status='active',
        payment_status='paid',
        due_date__isnull=False
    )
    
    now = timezone.now()
    notifications_sent = 0
    
    for rental in active_rentals:
        days_until_due = (rental.due_date - now).days
        
        # Send notification for 3 days, 2 days, and 1 day before due date
        if days_until_due in [3, 2, 1]:
            # Check if notification already sent today for this rental
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            already_sent = RentalNotification.objects.filter(
                rental=rental,
                notification_type='due_soon',
                created_at__gte=today_start
            ).exists()
            
            if not already_sent:
                # Send email
                try:
                    send_rental_due_soon_email(rental, days_until_due)
                    
                    # Create notification record
                    RentalNotification.objects.create(
                        rental=rental,
                        user=rental.user,
                        notification_type='due_soon',
                        title=f'Book Return Due in {days_until_due} Day(s)',
                        message=f'Your rental for "{rental.book.title}" is due on {rental.due_date.strftime("%Y-%m-%d")}. Please return the book on time to avoid late fees.',
                        is_sent=True,
                        sent_at=now
                    )
                    
                    notifications_sent += 1
                    logger.info(f"Due soon notification sent for rental {rental.rental_number} ({days_until_due} days)")
                except Exception as e:
                    logger.error(f"Error sending due soon notification for {rental.rental_number}: {str(e)}")
    
    logger.info(f"Checked due soon rentals: {notifications_sent} notifications sent")
    return notifications_sent


@shared_task
def check_overdue_rentals():
    """
    Check for overdue rentals, calculate late fees, and send notifications
    Runs daily to identify and notify about overdue rentals
    """
    from .models import BookRental, RentalSettings, RentalNotification, RentalStatusHistory
    from .email_utils import send_rental_overdue_email
    
    settings = RentalSettings.get_settings()
    
    # Get active rentals that are past due date
    now = timezone.now()
    overdue_rentals = BookRental.objects.filter(
        status='active',
        payment_status='paid',
        due_date__lt=now
    )
    
    notifications_sent = 0
    
    for rental in overdue_rentals:
        # Update status to overdue if not already
        if rental.status != 'overdue':
            rental.status = 'overdue'
            rental.save()
            
            # Create status history
            RentalStatusHistory.objects.create(
                rental=rental,
                status='overdue',
                notes=f'Rental became overdue. Due date was {rental.due_date.strftime("%Y-%m-%d")}'
            )
        
        # Calculate current late fee
        late_fee = rental.calculate_late_fee(settings.daily_late_fee)
        
        # Check if overdue notification sent today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        already_sent = RentalNotification.objects.filter(
            rental=rental,
            notification_type='overdue',
            created_at__gte=today_start
        ).exists()
        
        if not already_sent and settings.enable_notifications:
            # Send overdue email
            try:
                send_rental_overdue_email(rental)
                
                # Create notification record
                RentalNotification.objects.create(
                    rental=rental,
                    user=rental.user,
                    notification_type='overdue',
                    title=f'⚠️ Overdue: "{rental.book.title}"',
                    message=f'Your rental is {rental.overdue_days} day(s) overdue. Late fee: ৳{late_fee}. Please return the book as soon as possible.',
                    is_sent=True,
                    sent_at=now
                )
                
                notifications_sent += 1
                logger.info(f"Overdue notification sent for rental {rental.rental_number} - {rental.overdue_days} days late, fee: ৳{late_fee}")
            except Exception as e:
                logger.error(f"Error sending overdue notification for {rental.rental_number}: {str(e)}")
    
    logger.info(f"Checked overdue rentals: {overdue_rentals.count()} overdue, {notifications_sent} notifications sent")
    return notifications_sent


@shared_task
def update_overdue_status():
    """
    Update rental status to overdue for rentals past due date
    Runs every hour to keep status up to date
    """
    from .models import BookRental, RentalStatusHistory
    
    now = timezone.now()
    rentals = BookRental.objects.filter(
        status='active',
        due_date__lt=now
    )
    
    updated = 0
    for rental in rentals:
        rental.status = 'overdue'
        rental.save()
        
        # Create status history if not already created today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        history_exists = RentalStatusHistory.objects.filter(
            rental=rental,
            status='overdue',
            created_at__gte=today_start
        ).exists()
        
        if not history_exists:
            RentalStatusHistory.objects.create(
                rental=rental,
                status='overdue',
                notes=f'Automatically marked as overdue'
            )
        
        updated += 1
    
    logger.info(f"Updated {updated} rentals to overdue status")
    return updated


@shared_task
def calculate_all_late_fees():
    """
    Calculate late fees for all overdue rentals
    Runs daily to update late fee amounts
    """
    from .models import BookRental, RentalSettings
    
    settings = RentalSettings.get_settings()
    
    overdue_rentals = BookRental.objects.filter(
        status__in=['overdue', 'active'],
        due_date__lt=timezone.now()
    )
    
    total_fees = 0
    count = 0
    
    for rental in overdue_rentals:
        fee = rental.calculate_late_fee(settings.daily_late_fee)
        total_fees += fee
        count += 1
    
    logger.info(f"Calculated late fees for {count} rentals. Total fees: ৳{total_fees}")
    return {'count': count, 'total_fees': float(total_fees)}


@shared_task
def send_daily_rental_reminders():
    """
    Master task to run all daily rental checks
    This should be scheduled to run once per day (e.g., at 9:00 AM)
    """
    logger.info("Starting daily rental reminder tasks")
    
    # Check and send due soon notifications
    due_soon_count = check_due_soon_rentals()
    
    # Check and send overdue notifications
    overdue_count = check_overdue_rentals()
    
    # Calculate all late fees
    fee_result = calculate_all_late_fees()
    
    logger.info(f"Daily rental reminders completed: {due_soon_count} due soon, {overdue_count} overdue notifications sent")
    
    return {
        'due_soon_notifications': due_soon_count,
        'overdue_notifications': overdue_count,
        'late_fees_calculated': fee_result
    }
