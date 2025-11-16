"""
Rental Email Utility Functions
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_rental_confirmation_email(rental):
    """Send rental confirmation email"""
    subject = f'Rental Confirmation #{rental.rental_number} - BookStore'
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    html_message = render_to_string('emails/rental_confirmation.html', {
        'rental': rental,
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rental.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Rental confirmation email sent for {rental.rental_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending rental confirmation email: {str(e)}")
        return False


def send_rental_due_soon_email(rental, days_remaining):
    """Send reminder email when rental due date is approaching"""
    subject = f'Reminder: Book Return Due Soon - {rental.book.title}'
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    html_message = render_to_string('emails/rental_due_soon.html', {
        'rental': rental,
        'days_remaining': days_remaining,
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rental.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Due soon email sent for rental {rental.rental_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending due soon email: {str(e)}")
        return False


def send_rental_overdue_email(rental):
    """Send overdue notification email with late fee information"""
    from .models import RentalSettings
    
    settings_obj = RentalSettings.get_settings()
    late_fee = rental.calculate_late_fee(settings_obj.daily_late_fee)
    
    subject = f'⚠️ Overdue Notice: Please Return "{rental.book.title}"'
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    html_message = render_to_string('emails/rental_overdue.html', {
        'rental': rental,
        'late_fee': late_fee,
        'daily_late_fee': settings_obj.daily_late_fee,
        'overdue_days': rental.overdue_days,
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rental.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Overdue email sent for rental {rental.rental_number} - Late fee: ৳{late_fee}")
        return True
    except Exception as e:
        logger.error(f"Error sending overdue email: {str(e)}")
        return False


def send_rental_returned_email(rental):
    """Send email confirmation when book is returned"""
    subject = f'Book Return Confirmed - {rental.book.title}'
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    html_message = render_to_string('emails/rental_returned.html', {
        'rental': rental,
        'has_late_fee': rental.late_fee > 0,
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rental.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Return confirmation email sent for rental {rental.rental_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending return confirmation email: {str(e)}")
        return False


def send_rental_renewal_email(rental, additional_days):
    """Send email confirmation when rental is renewed"""
    subject = f'Rental Renewed - {rental.book.title}'
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    html_message = render_to_string('emails/rental_renewal.html', {
        'rental': rental,
        'additional_days': additional_days,
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rental.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Renewal confirmation email sent for rental {rental.rental_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending renewal email: {str(e)}")
        return False
