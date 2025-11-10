"""
Check if user has saved addresses
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from accounts.models import Address
from django.contrib.auth import get_user_model

User = get_user_model()

print("Checking user addresses...")
print("=" * 60)

# Get all users
users = User.objects.all()

for user in users:
    addresses = Address.objects.filter(user=user)
    print(f"\nUser: {user.email}")
    print(f"Total addresses: {addresses.count()}")
    
    if addresses.exists():
        for idx, addr in enumerate(addresses, 1):
            print(f"\n  Address #{idx}:")
            print(f"    ID: {addr.id}")
            print(f"    Name: {addr.full_name}")
            print(f"    Phone: {addr.phone}")
            print(f"    Address: {addr.address_line1}")
            print(f"    City: {addr.city}, {addr.state}")
            print(f"    Default: {'Yes' if addr.is_default else 'No'}")
    else:
        print("  ❌ No addresses saved")
        print("  👉 User needs to add an address at: /accounts/addresses/")

print("\n" + "=" * 60)
print("\nSUMMARY:")
total_addresses = Address.objects.count()
print(f"Total addresses in database: {total_addresses}")

if total_addresses == 0:
    print("\n⚠️  NO ADDRESSES FOUND!")
    print("This is why the checkout page shows empty form fields.")
    print("\nTO FIX:")
    print("1. Login to the site")
    print("2. Go to: http://127.0.0.1:8000/accounts/addresses/")
    print("3. Click 'Add New Address'")
    print("4. Fill in all fields and save")
    print("5. Return to checkout page")
