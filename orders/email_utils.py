"""
Email utility functions
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_order_confirmation_email(order):
    """Send order confirmation email"""
    subject = f'Order Confirmation - {order.order_number}'
    
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'order_items': order.items.all(),
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
