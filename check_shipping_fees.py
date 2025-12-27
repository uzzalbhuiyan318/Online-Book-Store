import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from orders.models import ShippingFee

print("=== CURRENT SHIPPING FEES IN DATABASE ===\n")
fees = ShippingFee.objects.all().order_by('-is_default', 'city_name')

for fee in fees:
    print(f"ID: {fee.id}")
    print(f"City: {fee.city_name}")
    print(f"City (Bangla): {fee.city_name_bn or 'N/A'}")
    print(f"Fee: ৳{fee.fee}")
    print(f"Is Default: {fee.is_default}")
    print(f"Is Active: {fee.is_active}")
    print(f"Updated: {fee.updated_at}")
    print("-" * 50)

print(f"\nTotal fees: {fees.count()}")
