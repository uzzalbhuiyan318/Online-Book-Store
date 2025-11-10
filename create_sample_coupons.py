"""
Test script to create sample coupons for the BookShop

This script creates various types of coupons that can be used in the checkout process.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from orders.models import Coupon

print("=== Creating Sample Coupons ===\n")

# Clear existing coupons (optional)
Coupon.objects.all().delete()
print("Cleared existing coupons\n")

# 1. Percentage discount coupon
coupon1 = Coupon.objects.create(
    code='WELCOME10',
    description='10% discount for new customers',
    discount_type='percentage',
    discount_value=10,
    min_purchase_amount=100,
    max_discount_amount=200,
    max_uses=100,
    max_uses_per_user=1,
    valid_from=timezone.now(),
    valid_to=timezone.now() + timedelta(days=30),
    is_active=True
)
print(f"✅ Created: {coupon1.code} - {coupon1.get_discount_display()} off (Min: ৳100, Max discount: ৳200)")

# 2. Fixed amount discount
coupon2 = Coupon.objects.create(
    code='SAVE50',
    description='Save ৳50 on your purchase',
    discount_type='fixed',
    discount_value=50,
    min_purchase_amount=200,
    max_uses=50,
    max_uses_per_user=2,
    valid_from=timezone.now(),
    valid_to=timezone.now() + timedelta(days=15),
    is_active=True
)
print(f"✅ Created: {coupon2.code} - {coupon2.get_discount_display()} off (Min: ৳200)")

# 3. Big discount percentage
coupon3 = Coupon.objects.create(
    code='MEGA20',
    description='20% discount - Limited time offer',
    discount_type='percentage',
    discount_value=20,
    min_purchase_amount=500,
    max_discount_amount=500,
    max_uses=20,
    max_uses_per_user=1,
    valid_from=timezone.now(),
    valid_to=timezone.now() + timedelta(days=7),
    is_active=True
)
print(f"✅ Created: {coupon3.code} - {coupon3.get_discount_display()} off (Min: ৳500, Max discount: ৳500)")

# 4. VIP coupon
coupon4 = Coupon.objects.create(
    code='VIP100',
    description='VIP Customer - ৳100 discount',
    discount_type='fixed',
    discount_value=100,
    min_purchase_amount=300,
    max_uses=None,  # Unlimited
    max_uses_per_user=5,
    valid_from=timezone.now(),
    valid_to=timezone.now() + timedelta(days=90),
    is_active=True
)
print(f"✅ Created: {coupon4.code} - {coupon4.get_discount_display()} off (Min: ৳300, Unlimited uses)")

# 5. Small discount
coupon5 = Coupon.objects.create(
    code='FIRST5',
    description='First purchase - ৳5 off',
    discount_type='fixed',
    discount_value=5,
    min_purchase_amount=50,
    max_uses=200,
    max_uses_per_user=1,
    valid_from=timezone.now(),
    valid_to=timezone.now() + timedelta(days=60),
    is_active=True
)
print(f"✅ Created: {coupon5.code} - {coupon5.get_discount_display()} off (Min: ৳50)")

print("\n=== Coupon Creation Complete! ===")
print(f"\nTotal coupons created: {Coupon.objects.count()}")
print("\nTest these coupons in the checkout page:")
print("  - WELCOME10: 10% off (min ৳100)")
print("  - SAVE50: ৳50 off (min ৳200)")
print("  - MEGA20: 20% off (min ৳500)")
print("  - VIP100: ৳100 off (min ৳300)")
print("  - FIRST5: ৳5 off (min ৳50)")
print("\nYou can manage these coupons in the Django Admin panel:")
print("http://127.0.0.1:8000/admin/orders/coupon/")
