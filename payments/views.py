from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Payment
from orders.models import Order, OrderStatusHistory
from .sslcommerz import SSLCommerzPayment
import logging

logger = logging.getLogger(__name__)


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
    """SSLCommerz success callback - handles both GET and POST"""
    # SSLCommerz sends data via both GET (user redirect) and POST (IPN)
    if request.method == 'POST':
        post_data = request.POST
    elif request.method == 'GET':
        post_data = request.GET
    else:
        logger.error("Invalid request method for SSLCommerz success callback")
        return redirect('books:home')
    
    transaction_id = post_data.get('tran_id')
    val_id = post_data.get('val_id')
    amount = post_data.get('amount')
    card_type = post_data.get('card_type', 'Unknown')
    
    if not transaction_id or not val_id:
        logger.error("Missing transaction_id or val_id in callback")
        messages.error(request, 'Invalid payment callback.')
        return redirect('books:home')
    
    try:
        # Initialize SSLCommerz payment gateway
        ssl = SSLCommerzPayment()
        
        # Verify hash for security (only for POST requests from SSLCommerz)
        if request.method == 'POST':
            if not ssl.verify_hash(post_data.dict()):
                logger.error(f"Hash verification failed for transaction {transaction_id}")
                messages.error(request, 'Payment verification failed.')
                return redirect('books:home')
        
        # Validate payment with SSLCommerz API
        logger.info(f"Validating payment with val_id: {val_id}")
        validation_response = ssl.validate_payment(val_id)
        
        logger.info(f"Validation response status: {validation_response.get('status')}")
        
        if validation_response.get('status') not in ['VALID', 'VALIDATED']:
            logger.error(f"Payment validation failed for transaction {transaction_id}. Response: {validation_response}")
            messages.error(request, 'Payment validation failed. Please contact support.')
            return redirect('books:home')
        
        # Get payment and order
        payment = Payment.objects.get(transaction_id=transaction_id)
        order = payment.order
        
        # Check if already processed (prevent duplicate processing)
        if payment.status == 'completed':
            logger.info(f"Payment already processed for transaction {transaction_id}")
            messages.success(request, 'Payment already completed!')
            return redirect('orders:order_success', order_number=order.order_number)
        
        # Verify amount matches
        validated_amount = validation_response.get('amount', amount)
        if float(validated_amount) != float(order.total):
            logger.error(f"Amount mismatch for order {order.order_number}: Expected {order.total}, Got {validated_amount}")
            messages.error(request, 'Payment amount mismatch. Please contact support.')
            return redirect('books:home')
        
        # Update payment status
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.gateway_response = validation_response
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
            notes=f'Payment successful via SSLCommerz. Transaction ID: {transaction_id}, Method: {card_type}',
        )
        
        logger.info(f"Payment successful for order {order.order_number}, transaction {transaction_id}")
        
        # Store success message in session (if session exists) or just redirect
        messages.success(request, 'Payment completed successfully!')
        
        # Redirect to order success page (now accessible without login for recent orders)
        return redirect('orders:order_success', order_number=order.order_number)
    
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for transaction {transaction_id}")
        messages.error(request, 'Payment not found. Please contact support.')
        return redirect('books:home')
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while processing payment. Please contact support.')
        return redirect('books:home')


@csrf_exempt
def sslcommerz_fail(request):
    """SSLCommerz fail callback - handles both GET and POST"""
    # SSLCommerz sends data via both GET (user redirect) and POST (IPN)
    if request.method == 'POST':
        post_data = request.POST
    elif request.method == 'GET':
        post_data = request.GET
    else:
        return redirect('books:home')
    
    transaction_id = post_data.get('tran_id')
    error_message = post_data.get('error', 'Payment failed')
    
    if not transaction_id:
        messages.error(request, 'Payment failed.')
        return redirect('books:home')
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        payment.status = 'failed'
        payment.gateway_response = post_data.dict() if hasattr(post_data, 'dict') else dict(post_data)
        payment.save()
        
        # Update order
        order = payment.order
        order.payment_status = 'failed'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes=f'Payment failed via SSLCommerz. Error: {error_message}',
        )
        
        logger.warning(f"Payment failed for transaction {transaction_id}: {error_message}")
        messages.error(request, f'Payment failed: {error_message}. Please try again.')
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for failed transaction {transaction_id}")
        messages.error(request, 'Payment failed.')
    except Exception as e:
        logger.error(f"Error processing payment failure: {str(e)}")
    
    # Redirect to home page since user might not be logged in after payment gateway redirect
    return redirect('books:home')


@csrf_exempt
def sslcommerz_cancel(request):
    """SSLCommerz cancel callback - handles both GET and POST"""
    # SSLCommerz sends data via both GET (user redirect) and POST (IPN)
    if request.method == 'POST':
        post_data = request.POST
    elif request.method == 'GET':
        post_data = request.GET
    else:
        return redirect('books:home')
    
    transaction_id = post_data.get('tran_id')
    
    if not transaction_id:
        messages.info(request, 'Payment cancelled.')
        return redirect('books:home')
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        payment.status = 'failed'
        payment.gateway_response = post_data.dict() if hasattr(post_data, 'dict') else dict(post_data)
        payment.save()
        
        # Update order
        order = payment.order
        order.payment_status = 'pending'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Payment cancelled by user via SSLCommerz',
        )
        
        logger.info(f"Payment cancelled for transaction {transaction_id}")
        messages.info(request, 'Payment cancelled. You can try again from your orders.')
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for cancelled transaction {transaction_id}")
        messages.info(request, 'Payment cancelled.')
    except Exception as e:
        logger.error(f"Error processing payment cancellation: {str(e)}")
    
    # Redirect to home page since user might not be logged in after payment gateway redirect
    return redirect('books:home')


@csrf_exempt
def sslcommerz_ipn(request):
    """SSLCommerz IPN (Instant Payment Notification)"""
    if request.method == 'POST':
        transaction_id = request.POST.get('tran_id')
        val_id = request.POST.get('val_id')
        status = request.POST.get('status')
        
        try:
            # Initialize SSLCommerz payment gateway
            ssl = SSLCommerzPayment()
            
            # Verify hash for security
            if not ssl.verify_hash(request.POST.dict()):
                logger.error(f"IPN: Hash verification failed for transaction {transaction_id}")
                return HttpResponse('Hash verification failed', status=400)
            
            # Validate payment with SSLCommerz
            validation_response = ssl.validate_payment(val_id)
            
            if validation_response.get('status') not in ['VALID', 'VALIDATED']:
                logger.error(f"IPN: Payment validation failed for transaction {transaction_id}")
                return HttpResponse('Validation failed', status=400)
            
            payment = Payment.objects.get(transaction_id=transaction_id)
            
            # Only update if not already completed
            if payment.status != 'completed' and status == 'VALID':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.gateway_response = validation_response
                payment.save()
                
                # Update order
                order = payment.order
                if order.payment_status != 'paid':
                    order.payment_status = 'paid'
                    order.status = 'confirmed'
                    order.confirmed_at = timezone.now()
                    order.save()
                    
                    # Create status history
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='confirmed',
                        notes=f'Payment confirmed via SSLCommerz IPN. Transaction ID: {transaction_id}',
                    )
                    
                    logger.info(f"IPN: Payment confirmed for order {order.order_number}")
            
            return HttpResponse('OK')
            
        except Payment.DoesNotExist:
            logger.error(f"IPN: Payment not found for transaction {transaction_id}")
            return HttpResponse('Payment not found', status=404)
        except Exception as e:
            logger.error(f"IPN: Error processing notification: {str(e)}")
            return HttpResponse('Error processing IPN', status=500)
    
    return HttpResponse('Invalid request', status=400)
