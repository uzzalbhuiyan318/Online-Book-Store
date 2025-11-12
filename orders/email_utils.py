"""
Email utility functions
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
from .pdf_generator import generate_invoice_pdf

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """Send order confirmation email with invoice PDF"""
    subject = f'Order Confirmation #{order.order_number} - BookStore'
    
    # Get site URL for links in email
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Render email HTML
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'order_items': order.items.all(),
        'site_url': site_url,
    })
    
    plain_message = strip_tags(html_message)
    
    # Create email with HTML content
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )
    email.attach_alternative(html_message, "text/html")
    
    # Generate invoice PDF using ReportLab
    try:
        pdf_content = generate_invoice_pdf(order)
        
        # Attach PDF to email
        email.attach(
            filename=f'Invoice_{order.order_number}.pdf',
            content=pdf_content,
            mimetype='application/pdf'
        )
        logger.info("Invoice PDF generated successfully for order %s", order.order_number)
    except Exception as e:  # noqa: broad-except
        logger.error("Error generating invoice PDF for order %s: %s", order.order_number, str(e))
        # Continue without PDF attachment if generation fails
    
    # Send email
    try:
        email.send(fail_silently=False)
        logger.info("Order confirmation email sent successfully for order %s", order.order_number)
        return True
    except Exception as e:  # noqa: broad-except
        logger.error("Error sending order confirmation email for order %s: %s", order.order_number, str(e))
        return False


def send_order_status_update_email(order, old_status, new_status):
    """Send order status update email"""
    subject = f'Order Status Update - {order.order_number}'
    
    html_message = render_to_string('emails/order_status_update.html', {
        'order': order,
        'old_status': old_status,
        'new_status': new_status,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_shipped_email(order):
    """Send order shipped email"""
    subject = f'Your Order Has Been Shipped - {order.order_number}'
    
    html_message = render_to_string('emails/order_shipped.html', {
        'order': order,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_delivered_email(order):
    """Send order delivered email"""
    subject = f'Your Order Has Been Delivered - {order.order_number}'
    
    html_message = render_to_string('emails/order_delivered.html', {
        'order': order,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to BookStore!'
    
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
