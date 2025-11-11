"""
Payment Gateway Utilities
"""
import requests
import hashlib
import json
from django.conf import settings
from django.urls import reverse
from .models import Payment
import uuid


def initiate_payment(order, payment_method):
    """
    Initiate payment with selected gateway
    Returns payment URL or None if failed
    """
    
    if payment_method == 'bkash':
        return initiate_bkash_payment(order)
    elif payment_method == 'nagad':
        return initiate_nagad_payment(order)
    elif payment_method == 'rocket':
        return initiate_rocket_payment(order)
    elif payment_method == 'sslcommerz':
        return initiate_sslcommerz_payment(order)
    elif payment_method == 'cod':
        return None  # No payment URL needed for COD
    
    return None


def initiate_bkash_payment(order):
    """
    Initiate bKash payment
    """
    try:
        config = settings.PAYMENT_GATEWAYS['bkash']
        
        # Generate transaction ID
        transaction_id = f"BKASH-{order.order_number}-{uuid.uuid4().hex[:8]}"
        
        # Get access token
        token_url = f"{config['base_url']}/checkout/token/grant"
        token_headers = {
            'Content-Type': 'application/json',
            'username': config['username'],
            'password': config['password'],
        }
        token_data = {
            'app_key': config['app_key'],
            'app_secret': config['app_secret'],
        }
        
        token_response = requests.post(token_url, headers=token_headers, json=token_data)
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            id_token = token_data.get('id_token')
            
            # Create payment
            payment_url = f"{config['base_url']}/checkout/payment/create"
            payment_headers = {
                'Content-Type': 'application/json',
                'authorization': id_token,
                'x-app-key': config['app_key'],
            }
            payment_data = {
                'mode': '0011',
                'payerReference': order.user.phone or order.shipping_phone,
                'callbackURL': settings.SITE_URL + reverse('payments:bkash_callback'),
                'amount': str(order.total),
                'currency': 'BDT',
                'intent': 'sale',
                'merchantInvoiceNumber': order.order_number,
            }
            
            payment_response = requests.post(payment_url, headers=payment_headers, json=payment_data)
            
            if payment_response.status_code == 200:
                payment_result = payment_response.json()
                
                # Create payment record
                Payment.objects.create(
                    order=order,
                    payment_method='bkash',
                    transaction_id=transaction_id,
                    amount=order.total,
                    gateway_response=payment_result,
                )
                
                # Update order
                order.transaction_id = transaction_id
                order.save()
                
                return payment_result.get('bkashURL')
        
        return None
    except Exception as e:
        print(f"bKash payment error: {str(e)}")
        return None


def initiate_nagad_payment(order):
    """
    Initiate Nagad payment
    Note: This is a simplified version. Actual implementation requires proper encryption.
    """
    try:
        config = settings.PAYMENT_GATEWAYS['nagad']
        
        # Generate transaction ID
        transaction_id = f"NAGAD-{order.order_number}-{uuid.uuid4().hex[:8]}"
        
        # Create payment record
        Payment.objects.create(
            order=order,
            payment_method='nagad',
            transaction_id=transaction_id,
            amount=order.total,
        )
        
        # Update order
        order.transaction_id = transaction_id
        order.save()
        
        # In production, implement proper Nagad API integration
        # This is a placeholder
        return None
    except Exception as e:
        print(f"Nagad payment error: {str(e)}")
        return None


def initiate_rocket_payment(order):
    """
    Initiate Rocket payment
    Note: Rocket uses similar flow to bKash/Nagad
    """
    try:
        # Generate transaction ID
        transaction_id = f"ROCKET-{order.order_number}-{uuid.uuid4().hex[:8]}"
        
        # Create payment record
        Payment.objects.create(
            order=order,
            payment_method='rocket',
            transaction_id=transaction_id,
            amount=order.total,
        )
        
        # Update order
        order.transaction_id = transaction_id
        order.save()
        
        # In production, implement proper Rocket API integration
        return None
    except Exception as e:
        print(f"Rocket payment error: {str(e)}")
        return None


def initiate_sslcommerz_payment(order):
    """
    Initiate SSLCommerz payment using custom implementation
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from .sslcommerz import SSLCommerzPayment
        from django.http import HttpRequest
        
        logger.info(f"Initiating SSLCommerz payment for order {order.order_number}")
        
        # Generate transaction ID (use order number + UUID for uniqueness)
        transaction_id = f"SSL-{order.order_number}-{uuid.uuid4().hex[:8]}"
        logger.info(f"Generated transaction ID: {transaction_id}")
        
        # Create payment record first
        Payment.objects.create(
            order=order,
            payment_method='sslcommerz',
            transaction_id=transaction_id,
            amount=order.total,
        )
        logger.info(f"Payment record created for transaction {transaction_id}")
        
        # Update order with transaction ID
        order.transaction_id = transaction_id
        order.save()
        
        # Initialize SSLCommerz payment gateway
        ssl = SSLCommerzPayment()
        logger.info("SSLCommerzPayment class initialized")
        
        # Pass the transaction_id to create_session
        # Create a minimal request object for URL building
        # In actual use, this will be called from a view with real request object
        # For now, we'll build the URLs manually
        session_data = ssl.create_session(order, None, transaction_id)
        logger.info(f"SSLCommerz session response: {session_data.get('status')}")
        
        if session_data.get('status') == 'SUCCESS':
            # Update payment record with session data
            payment = Payment.objects.get(transaction_id=transaction_id)
            payment.gateway_response = session_data
            payment.save()
            
            gateway_url = session_data.get('GatewayPageURL')
            logger.info(f"SSLCommerz payment URL generated: {gateway_url}")
            return gateway_url
        else:
            error_msg = session_data.get('failedreason', 'Unknown error')
            logger.error(f"SSLCommerz session creation failed: {error_msg}")
            print(f"SSLCommerz session creation failed: {session_data}")
            return None
        
    except Exception as e:
        logger.error(f"SSLCommerz payment error: {str(e)}", exc_info=True)
        print(f"SSLCommerz payment error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verify_payment(transaction_id, payment_method):
    """
    Verify payment status
    """
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        
        if payment_method == 'bkash':
            return verify_bkash_payment(payment)
        elif payment_method == 'sslcommerz':
            return verify_sslcommerz_payment(payment)
        
        return False
    except Payment.DoesNotExist:
        return False


def verify_bkash_payment(payment):
    """
    Verify bKash payment
    """
    # Implement bKash payment verification
    return False


def verify_sslcommerz_payment(payment):
    """
    Verify SSLCommerz payment
    """
    # Implement SSLCommerz payment verification
    return False
