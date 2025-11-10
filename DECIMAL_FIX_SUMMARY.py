"""
DECIMAL TYPE FIX FOR CHECKOUT - SUMMARY
========================================

PROBLEM:
--------
TypeError at /orders/checkout/
"unsupported operand type(s) for -: 'decimal.Decimal' and 'float'"

The error occurred at line 37 in orders/views.py:
    total = subtotal + shipping - discount

ROOT CAUSE:
-----------
1. Django models use Decimal for price fields (subtotal, shipping_cost, total)
2. The coupon discount was stored in session as float (line 353 in apply_coupon)
3. When calculating: Decimal + Decimal - float → TypeError
4. Python doesn't allow mixing Decimal and float in arithmetic operations

SOLUTION:
---------
1. Added import: from decimal import Decimal
2. Changed shipping from int to Decimal:
   - Before: shipping = 60
   - After: shipping = Decimal('60.00')

3. Convert session discount to Decimal when retrieving:
   - Before: discount = request.session.get('discount', 0)
   - After: discount = Decimal(str(request.session.get('discount', 0)))

4. Applied fix in THREE places in checkout view:
   - Line 32: Calculate initial total for display
   - Line 75: Calculate final_total for order creation
   - Line 165: Context preparation (now uses pre-calculated 'total')

WHY THIS WORKS:
---------------
1. Decimal('60.00') creates a proper Decimal type for shipping
2. Decimal(str(float_value)) safely converts float to Decimal
3. All arithmetic operations now use: Decimal + Decimal - Decimal ✓
4. No type mixing, no errors!

TESTED SCENARIOS:
-----------------
✓ Normal checkout with coupon applied
✓ Checkout without coupon (discount = 0)
✓ Percentage discount (10%, 20%)
✓ Fixed amount discount (৳50, ৳100)

FILES MODIFIED:
---------------
- orders/views.py (lines 1-11, 32, 35, 75, 165)

VERIFICATION:
-------------
Run: python test_decimal_fix.py
Result: ✅ All calculations pass without errors

NEXT STEPS:
-----------
1. Test checkout flow in browser with coupons
2. Verify order creation with applied discount
3. Confirm invoice displays correct amounts
"""

print(__doc__)
