"""
Create a test address for the admin user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from accounts.models import Address
from django.contrib.auth import get_user_model

User = get_user_model()

print("Creating test address...")
print("=" * 60)

# Get admin user
try:
    user = User.objects.get(email='admin@gmail.com')
    print(f"✓ Found user: {user.email}")
except User.DoesNotExist:
    print("❌ Admin user not found!")
    exit(1)

# Create test address
address = Address.objects.create(
    user=user,
    full_name="Admin User",
    phone="01712345678",
    email=user.email,
    address_line1="123 Main Street",
    address_line2="Apartment 4B",
    city="Dhaka",
    state="Dhaka Division",
    postal_code="1200",
    country="Bangladesh",
    is_default=True
)

print(f"\n✅ Address created successfully!")
print(f"   ID: {address.id}")
print(f"   Name: {address.full_name}")
print(f"   Phone: {address.phone}")
print(f"   Address: {address.address_line1}, {address.city}")
print(f"   Default: Yes")

# Create a second address for testing
address2 = Address.objects.create(
    user=user,
    full_name="Admin User",
    phone="01898765432",
    email=user.email,
    address_line1="456 Park Avenue",
    address_line2="",
    city="Chittagong",
    state="Chittagong Division",
    postal_code="4000",
    country="Bangladesh",
    is_default=False
)

print(f"\n✅ Second address created!")
print(f"   ID: {address2.id}")
print(f"   Name: {address2.full_name}")
print(f"   Phone: {address2.phone}")
print(f"   Address: {address2.address_line1}, {address2.city}")
print(f"   Default: No")

print("\n" + "=" * 60)
print("✅ TEST DATA READY!")
print("\nNOW YOU CAN:")
print("1. Go to: http://127.0.0.1:8000/orders/checkout/")
print("2. You'll see 2 addresses with radio buttons")
print("3. Select the SECOND address (Chittagong)")
print("4. Apply coupon 'WELCOME10'")
print("5. After reload, the Chittagong address should still be selected!")
print("\nThe sessionStorage fix will now work correctly! 🎉")
