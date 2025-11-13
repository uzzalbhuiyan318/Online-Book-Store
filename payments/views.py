from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Payment
from orders.models import Order, OrderStatusHistory
from rentals.models import BookRental, RentalStatusHistory
from orders.email_utils import send_order_confirmation_email
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
    """SSLCommerz success callback - handles both GET and POST for orders and rentals"""
    # SSLCommerz sends data via both GET (user redirect) and POST (IPN)
    if request.method == 'POST':
        post_data = request.POST
    elif request.method == 'GET':
        post_data = request.GET
    else:
        logger.error("Invalid request method for SSLCommerz success callback")
        messages.error(request, 'Invalid payment callback.')
        return redirect('books:home')
    
    transaction_id = post_data.get('tran_id')
    val_id = post_data.get('val_id')
    amount = post_data.get('amount')
    card_type = post_data.get('card_type', 'Unknown')
    payment_type = post_data.get('value_c', 'order')  # Type indicator from create_session
    
    # Log all callback data for debugging
    logger.info(f"SSLCommerz callback received - tran_id: {transaction_id}, val_id: {val_id}, type: {payment_type}")
    logger.info(f"All callback params: {dict(post_data)}")
    
    if not transaction_id or not val_id:
        logger.error("Missing transaction_id or val_id in callback")
        messages.error(request, 'Invalid payment callback. Please check your status.')
        return redirect('books:home')
    
    try:
        # Get payment - it will have the reference to order or rental
        payment = None
        reference_obj = None  # Will be either Order or BookRental
        is_rental = payment_type == 'rental'
        
        try:
            # Try to find payment by transaction_id first
            payment = Payment.objects.get(transaction_id=transaction_id)
            
            if payment.order:
                reference_obj = payment.order
                is_rental = False
            elif payment.rental:
                reference_obj = payment.rental
                is_rental = True
            
            logger.info(f"Found payment by transaction_id: {transaction_id}, type: {'rental' if is_rental else 'order'}")
        except Payment.DoesNotExist:
            # If not found, try to extract reference from transaction_id
            logger.warning(f"Payment not found with transaction_id: {transaction_id}")
            
            # Try extracting reference number from transaction_id format SSL-{number}-{uuid}
            if transaction_id and transaction_id.startswith('SSL-'):
                parts = transaction_id.split('-')
                if len(parts) >= 2:
                    reference_number = '-'.join(parts[1:-1])
                    
                    # Try rental first if payment_type indicates rental
                    if is_rental:
                        try:
                            reference_obj = BookRental.objects.get(rental_number=reference_number)
                            payment = Payment.objects.filter(rental=reference_obj, payment_method='sslcommerz').latest('created_at')
                            logger.info(f"Found rental {reference_number} by extracting from transaction_id")
                        except (BookRental.DoesNotExist, Payment.DoesNotExist):
                            pass
                    
                    # If not rental or not found, try order
                    if not reference_obj:
                        try:
                            reference_obj = Order.objects.get(order_number=reference_number)
                            payment = Payment.objects.filter(order=reference_obj, payment_method='sslcommerz').latest('created_at')
                            is_rental = False
                            logger.info(f"Found order {reference_number} by extracting from transaction_id")
                        except (Order.DoesNotExist, Payment.DoesNotExist):
                            pass
            
            if not payment or not reference_obj:
                raise Payment.DoesNotExist("Cannot find payment or reference")
        
        # Initialize SSLCommerz payment gateway
        ssl = SSLCommerzPayment()
        
        # Verify hash for security (only for POST requests from SSLCommerz)
        if request.method == 'POST':
            post_data_dict = {k: v for k, v in post_data.items()}
            if not ssl.verify_hash(post_data_dict):
                logger.error(f"Hash verification failed for transaction {transaction_id}")
                logger.warning(f"Continuing with payment validation despite hash verification failure")
        
        # Validate payment with SSLCommerz API
        logger.info(f"Validating payment with val_id: {val_id}")
        validation_response = ssl.validate_payment(val_id)
        
        logger.info(f"Validation response status: {validation_response.get('status')}")
        
        if validation_response.get('status') not in ['VALID', 'VALIDATED']:
            logger.error(f"Payment validation failed for transaction {transaction_id}. Response: {validation_response}")
            messages.error(request, 'Payment validation failed. Please contact support if the amount was deducted.')
            
            # Redirect based on type
            if is_rental:
                return redirect('rentals:rental_success', rental_number=reference_obj.rental_number)
            else:
                return redirect('orders:order_success', order_number=reference_obj.order_number)
        
        # Check if already processed (prevent duplicate processing)
        if payment.status == 'completed':
            logger.info(f"Payment already processed for transaction {transaction_id}")
            messages.success(request, 'Payment already completed!')
            
            # Redirect based on type
            if is_rental:
                return redirect('rentals:rental_success', rental_number=reference_obj.rental_number)
            else:
                return redirect('orders:order_success', order_number=reference_obj.order_number)
        
        # Verify amount matches
        validated_amount = validation_response.get('amount', amount)
        expected_amount = reference_obj.total_amount if is_rental else reference_obj.total
        
        if float(validated_amount) != float(expected_amount):
            logger.error(f"Amount mismatch: Expected {expected_amount}, Got {validated_amount}")
            messages.warning(request, 'Payment amount mismatch detected. Please contact support.')
            
            # Redirect based on type
            if is_rental:
                return redirect('rentals:rental_success', rental_number=reference_obj.rental_number)
            else:
                return redirect('orders:order_success', order_number=reference_obj.order_number)
        
        # Update payment status
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.gateway_response = validation_response
        payment.save()
        
        # Update reference object status based on type
        if is_rental:
            reference_obj.payment_status = 'paid'
            reference_obj.status = 'active'
            reference_obj.save()
            
            # Create rental status history
            RentalStatusHistory.objects.create(
                rental=reference_obj,
                status='active',
                notes=f'Payment successful via SSLCommerz. Transaction ID: {transaction_id}, Method: {card_type}',
            )
            
            logger.info(f"Payment successful for rental {reference_obj.rental_number}, transaction {transaction_id}")
            messages.success(request, 'Payment completed successfully! Your rental is now active.')
            
            return redirect('rentals:rental_success', rental_number=reference_obj.rental_number)
        else:
            reference_obj.payment_status = 'paid'
            reference_obj.status = 'confirmed'
            reference_obj.confirmed_at = timezone.now()
            reference_obj.save()
            
            # Create order status history
            OrderStatusHistory.objects.create(
                order=reference_obj,
                status='confirmed',
                notes=f'Payment successful via SSLCommerz. Transaction ID: {transaction_id}, Method: {card_type}',
            )
            
            logger.info(f"Payment successful for order {reference_obj.order_number}, transaction {transaction_id}")
            
            # Send order confirmation email
            logger.info(f"SSLCommerz payment successful, attempting to send email to {reference_obj.user.email}")
            try:
                result = send_order_confirmation_email(reference_obj)
                if result:
                    logger.info(f"✅ Order confirmation email sent successfully for order {reference_obj.order_number}")
                else:
                    logger.warning(f"⚠️ Email function returned False for order {reference_obj.order_number}")
            except Exception as e:
                logger.error(f"❌ Failed to send confirmation email: {str(e)}")
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('orders:order_success', order_number=reference_obj.order_number)
    
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for transaction {transaction_id}")
        messages.error(request, 'Payment record not found. Please check your status.')
        return redirect('books:home')
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while processing payment. Please contact support if amount was deducted.')
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
    payment_type = post_data.get('value_c', 'order')
    
    if not transaction_id:
        messages.error(request, 'Payment failed.')
        return redirect('books:home')
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        payment.status = 'failed'
        payment.gateway_response = post_data.dict() if hasattr(post_data, 'dict') else dict(post_data)
        payment.save()
        
        # Check if this is a rental or order
        if payment.rental:
            rental = payment.rental
            rental.payment_status = 'failed'
            rental.save()
            
            RentalStatusHistory.objects.create(
                rental=rental,
                status='pending',
                notes=f'Payment failed via SSLCommerz. Error: {error_message}',
            )
            
            logger.warning(f"Payment failed for rental {rental.rental_number}: {error_message}")
            messages.error(request, f'Payment failed: {error_message}. You can retry payment from your rental details.')
            
            return redirect('rentals:rental_success', rental_number=rental.rental_number)
        else:
            order = payment.order
            order.payment_status = 'failed'
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes=f'Payment failed via SSLCommerz. Error: {error_message}',
            )
            
            logger.warning(f"Payment failed for order {order.order_number}: {error_message}")
            messages.error(request, f'Payment failed: {error_message}. You can retry payment from your order details.')
            
            return redirect('orders:order_success', order_number=order.order_number)
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for failed transaction {transaction_id}")
        messages.error(request, 'Payment failed.')
    except Exception as e:
        logger.error(f"Error processing payment failure: {str(e)}")
    
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
        
        # Check if this is a rental or order
        if payment.rental:
            rental = payment.rental
            rental.payment_status = 'pending'
            rental.save()
            
            RentalStatusHistory.objects.create(
                rental=rental,
                status='pending',
                notes='Payment cancelled by user via SSLCommerz',
            )
            
            logger.info(f"Payment cancelled for rental {rental.rental_number}")
            messages.info(request, 'Payment cancelled. You can retry payment from your rental details.')
            
            return redirect('rentals:rental_success', rental_number=rental.rental_number)
        else:
            order = payment.order
            order.payment_status = 'pending'
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Payment cancelled by user via SSLCommerz',
            )
            
            logger.info(f"Payment cancelled for order {order.order_number}")
            messages.info(request, 'Payment cancelled. You can retry payment from your order details.')
            
            return redirect('orders:order_success', order_number=order.order_number)
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for cancelled transaction {transaction_id}")
        messages.info(request, 'Payment cancelled.')
    except Exception as e:
        logger.error(f"Error processing payment cancellation: {str(e)}")
    
    return redirect('books:home')


@csrf_exempt
def sslcommerz_ipn(request):
    """SSLCommerz IPN (Instant Payment Notification) - handles both orders and rentals"""
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
                
                # Check if this is a rental or order
                if payment.rental:
                    rental = payment.rental
                    if rental.payment_status != 'paid':
                        rental.payment_status = 'paid'
                        rental.status = 'active'
                        rental.save()
                        
                        RentalStatusHistory.objects.create(
                            rental=rental,
                            status='active',
                            notes=f'Payment confirmed via SSLCommerz IPN. Transaction ID: {transaction_id}',
                        )
                        
                        logger.info(f"IPN: Payment confirmed for rental {rental.rental_number}")
                else:
                    order = payment.order
                    if order.payment_status != 'paid':
                        order.payment_status = 'paid'
                        order.status = 'confirmed'
                        order.confirmed_at = timezone.now()
                        order.save()
                        
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
