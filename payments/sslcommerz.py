"""
SSLCommerz Payment Gateway Integration
"""
import requests
import hashlib
from decimal import Decimal
from django.conf import settings
from django.urls import reverse


class SSLCommerzPayment:
    """SSLCommerz Payment Gateway Handler"""
    
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_password = settings.SSLCOMMERZ_STORE_PASSWORD
        self.is_sandbox = settings.SSLCOMMERZ_IS_SANDBOX
        
        if self.is_sandbox:
            self.base_url = 'https://sandbox.sslcommerz.com'
        else:
            self.base_url = 'https://securepay.sslcommerz.com'
    
    def create_session(self, order, request=None, transaction_id=None):
        """
        Create payment session with SSLCommerz
        
        Args:
            order: Order instance
            request: Django request object (optional)
            transaction_id: Custom transaction ID (optional, defaults to order_number)
            
        Returns:
            dict: Response from SSLCommerz API
        """
        # Use provided transaction_id or fallback to order_number
        tran_id = transaction_id if transaction_id else order.order_number
        
        # Build absolute URLs for callbacks
        if request:
            success_url = request.build_absolute_uri(reverse('payments:sslcommerz_success'))
            fail_url = request.build_absolute_uri(reverse('payments:sslcommerz_fail'))
            cancel_url = request.build_absolute_uri(reverse('payments:sslcommerz_cancel'))
            ipn_url = request.build_absolute_uri(reverse('payments:sslcommerz_ipn'))
        else:
            # Fallback to settings if request is not available
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            success_url = f"{base_url}{reverse('payments:sslcommerz_success')}"
            fail_url = f"{base_url}{reverse('payments:sslcommerz_fail')}"
            cancel_url = f"{base_url}{reverse('payments:sslcommerz_cancel')}"
            ipn_url = f"{base_url}{reverse('payments:sslcommerz_ipn')}"
        
        # Prepare payment data
        post_data = {
            # Store Information
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            
            # Transaction Information
            'total_amount': str(order.total),
            'currency': 'BDT',
            'tran_id': tran_id,  # Use the transaction_id parameter
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'ipn_url': ipn_url,
            
            # Customer Information - ensure all required fields are properly set
            'cus_name': order.shipping_full_name or f"{order.user.first_name} {order.user.last_name}".strip() or "Customer",
            'cus_email': order.shipping_email or order.user.email or 'customer@example.com',
            'cus_add1': order.shipping_address_line1 or 'Address',
            'cus_add2': order.shipping_address_line2 or '',
            'cus_city': order.shipping_city or 'Dhaka',
            'cus_state': order.shipping_state or 'Dhaka',
            'cus_postcode': order.shipping_postal_code or '1000',
            'cus_country': order.shipping_country or 'Bangladesh',
            'cus_phone': order.shipping_phone or '01700000000',
            'cus_fax': '',
            
            # Shipment Information - ensure all fields are set
            'shipping_method': 'YES',
            'ship_name': order.shipping_full_name or f"{order.user.first_name} {order.user.last_name}".strip() or "Customer",
            'ship_add1': order.shipping_address_line1 or 'Address',
            'ship_add2': order.shipping_address_line2 or '',
            'ship_city': order.shipping_city or 'Dhaka',
            'ship_state': order.shipping_state or 'Dhaka',
            'ship_postcode': order.shipping_postal_code or '1000',
            'ship_country': order.shipping_country or 'Bangladesh',
            
            # Product Information
            'product_name': f'Order #{order.order_number}',
            'product_category': 'Books',
            'product_profile': 'physical-goods',
            
            # Additional Information
            'value_a': order.order_number,  # Order reference
            'value_b': str(order.user.id),  # User ID
            'value_c': '',
            'value_d': '',
        }
        
        try:
            # Make API request to SSLCommerz
            response = requests.post(
                f'{self.base_url}/gwprocess/v4/api.php',
                data=post_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'FAILED',
                    'failedreason': f'HTTP {response.status_code}: {response.text}'
                }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'FAILED',
                'failedreason': f'Connection error: {str(e)}'
            }
    
    def validate_payment(self, val_id):
        """
        Validate payment with SSLCommerz
        
        Args:
            val_id: Validation ID from SSLCommerz
            
        Returns:
            dict: Validation response
        """
        validation_url = f'{self.base_url}/validator/api/validationserverAPI.php'
        
        params = {
            'val_id': val_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(validation_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'INVALID'}
        except requests.exceptions.RequestException:
            return {'status': 'INVALID'}
    
    def verify_hash(self, post_data):
        """
        Verify hash value from SSLCommerz IPN
        
        Args:
            post_data: POST data from SSLCommerz
            
        Returns:
            bool: True if hash is valid
        """
        verify_sign = post_data.get('verify_sign', '')
        verify_key = post_data.get('verify_key', '')
        
        if not verify_sign or not verify_key:
            return False
        
        # Get all keys except verify_sign and verify_key
        keys_to_hash = [k for k in sorted(post_data.keys()) 
                       if k not in ['verify_sign', 'verify_key']]
        
        # Build hash string
        hash_string = '&'.join([f'{k}={post_data[k]}' for k in keys_to_hash])
        hash_string = self.store_password + hash_string
        
        # Calculate MD5 hash
        calculated_hash = hashlib.md5(hash_string.encode()).hexdigest()
        
        return calculated_hash == verify_sign
    
    def initiate_refund(self, bank_tran_id, refund_amount, refund_remarks):
        """
        Initiate refund through SSLCommerz
        
        Args:
            bank_tran_id: Bank transaction ID from SSLCommerz
            refund_amount: Amount to refund
            refund_remarks: Reason for refund
            
        Returns:
            dict: Refund response
        """
        refund_url = f'{self.base_url}/validator/api/merchantTransIDvalidationAPI.php'
        
        post_data = {
            'refund_amount': str(refund_amount),
            'refund_remarks': refund_remarks,
            'bank_tran_id': bank_tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
        }
        
        try:
            response = requests.post(refund_url, data=post_data, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'failed'}
        except requests.exceptions.RequestException:
            return {'status': 'failed'}
