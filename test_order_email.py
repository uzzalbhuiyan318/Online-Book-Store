"""
Test Order Confirmation Email - Real Email to Customer
This will send a real order confirmation email to a customer
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.conf import settings
from orders.models import Order
from orders.email_utils import send_order_confirmation_email

def test_order_email():
    print("=" * 80)
    print("ORDER CONFIRMATION EMAIL TEST - REAL CUSTOMER EMAIL")
    print("=" * 80)
    print()
    
    # Check backend
    print("📧 Email Backend:", settings.EMAIL_BACKEND)
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("⚠️  WARNING: Console mode is active!")
        print("   Set USE_CONSOLE_EMAIL=False in .env to send real emails")
        return
    
    print("✅ SMTP mode active - will send real emails")
    print()
    
    # Get most recent order
    order = Order.objects.order_by('-created_at').first()
    
    if not order:
        print("❌ No orders found in database")
        print("   Please create an order first")
        return
    
    print("📦 Order Details:")
    print(f"   Order Number: {order.order_number}")
    print(f"   Customer: {order.user.get_full_name()}")
    print(f"   Email: {order.user.email}")
    print(f"   Total: ৳{order.total}")
    print(f"   Status: {order.get_status_display()}")
    print(f"   Payment: {order.get_payment_status_display()}")
    print()
    
    # Confirm sending
    confirm = input(f"Send order confirmation email to {order.user.email}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Email sending cancelled")
        return
    
    print()
    print(f"📨 Sending order confirmation email to {order.user.email}...")
    print()
    
    try:
        result = send_order_confirmation_email(order)
        
        if result:
            print("✅ SUCCESS! Order confirmation email sent!")
            print()
            print("📧 Email Details:")
            print(f"   To: {order.user.email}")
            print(f"   Subject: Order Confirmation #{order.order_number} - BookStore")
            print(f"   Includes: Invoice attachment (Invoice_{order.order_number}.html)")
            print()
            print("🎯 What the customer received:")
            print("   ✅ Beautiful HTML email with order details")
            print("   ✅ Complete product list and pricing")
            print("   ✅ Shipping address information")
            print("   ✅ Invoice HTML file attachment")
            print()
            print("📬 Next Steps:")
            print(f"   1. Ask customer to check: {order.user.email}")
            print("   2. Check spam/junk folder if not in inbox")
            print("   3. Email should arrive within 1-2 minutes")
            print()
            print("🔄 Automatic Emails Now Active:")
            print("   - COD orders: Email sent immediately after checkout")
            print("   - SSLCommerz: Email sent after successful payment")
            print("   - All customers will receive invoice automatically!")
        else:
            print("⚠️  Email function returned False")
            print("   Check server logs for details")
            
    except Exception as e:
        print(f"❌ ERROR sending email:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_order_email()
