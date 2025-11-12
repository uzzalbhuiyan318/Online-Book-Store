"""
Test script to verify PDF invoice generation and email sending
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from orders.models import Order
from orders.email_utils import send_order_confirmation_email
from django.conf import settings

print("=" * 70)
print("PDF INVOICE EMAIL TEST")
print("=" * 70)
print()

# Step 1: Check email configuration
print("📧 STEP 1: Email Configuration")
print("-" * 70)
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"Email From: {settings.DEFAULT_FROM_EMAIL}")
print(f"Use Console Email: {getattr(settings, 'USE_CONSOLE_EMAIL', 'Not set')}")
print()

# Step 2: Get recent orders
print("📦 STEP 2: Finding Recent Orders")
print("-" * 70)
recent_orders = Order.objects.all().order_by('-created_at')[:5]
print(f"Found {recent_orders.count()} recent orders")
for order in recent_orders:
    print(f"  - Order #{order.order_number} | User: {order.user.email} | Total: ৳{order.total}")
print()

if not recent_orders:
    print("❌ No orders found in database. Please create an order first.")
    sys.exit(1)

# Step 3: Test PDF generation and email sending
print("📄 STEP 3: Testing PDF Invoice Email")
print("-" * 70)
test_order = recent_orders.first()
print(f"Testing with Order #{test_order.order_number}")
print(f"Customer Email: {test_order.user.email}")
print()

print("Attempting to send email with PDF invoice...")
result = send_order_confirmation_email(test_order)

if result:
    print("✅ SUCCESS: Email with PDF invoice sent successfully!")
    print(f"   Check inbox at: {test_order.user.email}")
    print(f"   Attachment: Invoice_{test_order.order_number}.pdf")
else:
    print("❌ FAILED: Email sending failed. Check logs for details.")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print()
print("📌 WHAT TO CHECK IN YOUR EMAIL:")
print("   1. Email subject: Order Confirmation #[order number] - BookStore")
print("   2. Email body with order details (HTML formatted)")
print("   3. PDF attachment named: Invoice_[order number].pdf")
print("   4. PDF should open properly (not show HTML code)")
print()
