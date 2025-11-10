from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Payment
from orders.models import Order, OrderStatusHistory


def bkash_callback(request):
    """bKash payment callback"""
    payment_id = request.GET.get('paymentID')
    status = request.GET.get('status')
    
    if status == 'success':
        # Handle successful payment
        # In production, verify payment with bKash API
        return redirect('payments:bkash_execute')
    else:
        messages.error(request, 'Payment was not successful.')
        return redirect('orders:my_orders')


def bkash_execute(request):
    """Execute bKash payment"""
    # In production, execute payment with bKash API
    messages.success(request, 'Payment completed successfully!')
    return redirect('orders:my_orders')


def nagad_callback(request):
    """Nagad payment callback"""
    # Handle Nagad callback
    messages.success(request, 'Payment completed successfully!')
    return redirect('orders:my_orders')


def rocket_callback(request):
    """Rocket payment callback"""
    # Handle Rocket callback
    messages.success(request, 'Payment completed successfully!')
    return redirect('orders:my_orders')


@csrf_exempt
def sslcommerz_success(request):
    """SSLCommerz success callback"""
    if request.method == 'POST':
        transaction_id = request.POST.get('tran_id')
        val_id = request.POST.get('val_id')
        amount = request.POST.get('amount')
        card_type = request.POST.get('card_type')
        
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            order = payment.order
            
            # Update payment status
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.gateway_response = request.POST.dict()
            payment.save()
            
            # Update order status
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='confirmed',
                notes='Payment successful via SSLCommerz',
            )
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('orders:order_success', order_number=order.order_number)
        
        except Payment.DoesNotExist:
            messages.error(request, 'Payment not found.')
            return redirect('orders:my_orders')
    
    return redirect('orders:my_orders')


@csrf_exempt
def sslcommerz_fail(request):
    """SSLCommerz fail callback"""
    transaction_id = request.POST.get('tran_id')
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        payment.status = 'failed'
        payment.gateway_response = request.POST.dict()
        payment.save()
        
        messages.error(request, 'Payment failed. Please try again.')
    except Payment.DoesNotExist:
        pass
    
    return redirect('orders:my_orders')


@csrf_exempt
def sslcommerz_cancel(request):
    """SSLCommerz cancel callback"""
    transaction_id = request.POST.get('tran_id')
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        payment.status = 'failed'
        payment.gateway_response = request.POST.dict()
        payment.save()
        
        messages.info(request, 'Payment cancelled.')
    except Payment.DoesNotExist:
        pass
    
    return redirect('orders:my_orders')


@csrf_exempt
def sslcommerz_ipn(request):
    """SSLCommerz IPN (Instant Payment Notification)"""
    if request.method == 'POST':
        transaction_id = request.POST.get('tran_id')
        val_id = request.POST.get('val_id')
        
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            
            if payment.status != 'completed':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.gateway_response = request.POST.dict()
                payment.save()
                
                # Update order
                order = payment.order
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.confirmed_at = timezone.now()
                order.save()
            
            return HttpResponse('OK')
        except Payment.DoesNotExist:
            return HttpResponse('Payment not found', status=404)
    
    return HttpResponse('Invalid request', status=400)
