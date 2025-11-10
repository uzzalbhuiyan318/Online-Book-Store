"""
Celery tasks for asynchronous operations
"""
from celery import shared_task
from django.core.mail import send_mail
from orders.email_utils import (
    send_order_confirmation_email,
    send_order_status_update_email,
    send_order_shipped_email,
    send_order_delivered_email,
)


@shared_task
def send_order_confirmation_task(order_id):
    """Send order confirmation email task"""
    from orders.models import Order
    try:
        order = Order.objects.get(id=order_id)
        send_order_confirmation_email(order)
    except Order.DoesNotExist:
        pass


@shared_task
def send_order_status_update_task(order_id, old_status, new_status):
    """Send order status update email task"""
    from orders.models import Order
    try:
        order = Order.objects.get(id=order_id)
        send_order_status_update_email(order, old_status, new_status)
    except Order.DoesNotExist:
        pass


@shared_task
def send_order_shipped_task(order_id):
    """Send order shipped email task"""
    from orders.models import Order
    try:
        order = Order.objects.get(id=order_id)
        send_order_shipped_email(order)
    except Order.DoesNotExist:
        pass


@shared_task
def send_order_delivered_task(order_id):
    """Send order delivered email task"""
    from orders.models import Order
    try:
        order = Order.objects.get(id=order_id)
        send_order_delivered_email(order)
    except Order.DoesNotExist:
        pass
