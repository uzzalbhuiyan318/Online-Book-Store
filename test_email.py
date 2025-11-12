"""
Email Configuration Test Script
Run this to test your email setup before placing real orders
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from orders.models import Order
from orders.email_utils import send_order_confirmation_email

def test_email_settings():
    """Test email configuration"""
    print("=" * 80)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 80)
    print()
    
    # Show current settings
    print("📧 Current Email Settings:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print(f"   MODE: Console (emails will print in terminal)")
        print()
        print("✅ Console mode is active - emails will be printed below:")
        print()
    else:
        print(f"   MODE: SMTP (real emails will be sent)")
        print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print()
    
    print("-" * 80)
    
    # Test 1: Simple email
    print("\n🧪 TEST 1: Sending a simple test email...")
    try:
        send_mail(
            subject='Test Email from BookStore',
            message='This is a test email to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print("✅ Simple email test PASSED!")
    except Exception as e:
        print(f"❌ Simple email test FAILED: {str(e)}")
        return False
    
    print("-" * 80)
    
    # Test 2: Order confirmation email
    print("\n🧪 TEST 2: Testing order confirmation email...")
    try:
        # Get the most recent order
        order = Order.objects.order_by('-created_at').first()
        
        if not order:
            print("⚠️  No orders found in database. Create an order first to test.")
            print("   You can skip this test for now.")
            return True
        
        print(f"   Using order: {order.order_number}")
        print(f"   Customer: {order.user.email}")
        print(f"   Total: ৳{order.total}")
        print()
        
        # Send order confirmation
        result = send_order_confirmation_email(order)
        
        if result:
            print("✅ Order confirmation email test PASSED!")
            print("   Email includes invoice attachment")
        else:
            print("⚠️  Order confirmation email returned False (check logs)")
            
    except Exception as e:
        print(f"❌ Order confirmation email test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("-" * 80)
    print()
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("✅ All tests passed!")
        print()
        print("📝 NOTES:")
        print("   - You're in CONSOLE mode - emails are printed above")
        print("   - Check the terminal output to see email content")
        print("   - To send real emails, set USE_CONSOLE_EMAIL=False in .env")
        print()
        print("🔄 TO SWITCH TO REAL EMAIL MODE:")
        print("   1. Create/edit .env file")
        print("   2. Add: USE_CONSOLE_EMAIL=False")
        print("   3. Restart server")
        print("   4. Run this test again")
    else:
        print("✅ All tests passed!")
        print()
        print("📧 SMTP mode is active - real emails were sent!")
        print(f"   Check inbox: {order.user.email if order else 'test@example.com'}")
        print()
        print("🔄 TO SWITCH TO CONSOLE MODE (for testing):")
        print("   1. Edit .env file")
        print("   2. Add: USE_CONSOLE_EMAIL=True")
        print("   3. Restart server")
    
    print("=" * 80)
    return True


if __name__ == '__main__':
    test_email_settings()
