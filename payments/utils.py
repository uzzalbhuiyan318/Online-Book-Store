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
    Initiate SSLCommerz payment
    """
    try:
        from sslcommerz_python.payment import SSLCSession
        
        config = settings.PAYMENT_GATEWAYS['sslcommerz']
        
        # Generate transaction ID
        transaction_id = f"SSL-{order.order_number}-{uuid.uuid4().hex[:8]}"
        
        # Initialize SSLCommerz
        sslcz = SSLCSession(
            sslc_is_sandbox=config['is_sandbox'],
            sslc_store_id=config['store_id'],
            sslc_store_pass=config['store_password']
        )
        
        # Set URLs
        sslcz.set_urls(
            success_url=settings.SITE_URL + reverse('payments:sslcommerz_success'),
            fail_url=settings.SITE_URL + reverse('payments:sslcommerz_fail'),
            cancel_url=settings.SITE_URL + reverse('payments:sslcommerz_cancel'),
            ipn_url=settings.SITE_URL + reverse('payments:sslcommerz_ipn'),
        )
        
        # Set product and customer info
        sslcz.set_product_integration(
            total_amount=float(order.total),
            currency='BDT',
            product_category='books',
            product_name=f"Order {order.order_number}",
            num_of_item=order.items.count(),
            shipping_method='Courier',
            product_profile='general',
        )
        
        sslcz.set_customer_info(
            name=order.shipping_full_name,
            email=order.shipping_email or order.user.email,
            address1=order.shipping_address_line1,
            address2=order.shipping_address_line2,
            city=order.shipping_city,
            postcode=order.shipping_postal_code,
            country='Bangladesh',
            phone=order.shipping_phone,
        )
        
        sslcz.set_shipping_info(
            shipping_method='Courier',
            num_of_item=order.items.count(),
            name=order.shipping_full_name,
            address1=order.shipping_address_line1,
            address2=order.shipping_address_line2,
            city=order.shipping_city,
            postcode=order.shipping_postal_code,
            country='Bangladesh',
        )
        
        # Initiate payment
        response = sslcz.init_payment(transaction_id, 'BDT', float(order.total))
        
        if response.get('status') == 'SUCCESS':
            # Create payment record
            Payment.objects.create(
                order=order,
                payment_method='sslcommerz',
                transaction_id=transaction_id,
                amount=order.total,
                gateway_response=response,
            )
            
            # Update order
            order.transaction_id = transaction_id
            order.save()
            
            return response.get('GatewayPageURL')
        
        return None
    except Exception as e:
        print(f"SSLCommerz payment error: {str(e)}")
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
