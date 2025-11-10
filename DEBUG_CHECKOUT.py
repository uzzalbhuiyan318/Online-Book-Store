"""
DEBUGGING STEPS FOR CHECKOUT ADDRESS ISSUE
===========================================

To debug the address preservation issue, follow these steps:

1. OPEN BROWSER CONSOLE:
   - Chrome/Edge: Press F12 or Ctrl+Shift+I
   - Firefox: Press F12 or Ctrl+Shift+K
   - Look for the "Console" tab

2. GO TO CHECKOUT PAGE:
   - Navigate to: http://127.0.0.1:8000/orders/checkout/
   - Make sure you have items in cart

3. CHECK IF ADDRESSES ARE DISPLAYED:
   - Look at the page - do you see saved addresses with radio buttons?
   - OR do you see empty form fields (Full Name, Phone, Address, etc.)?
   
   IF YOU SEE EMPTY FORM FIELDS:
   - The issue is that no addresses are saved in database
   - Go to: http://127.0.0.1:8000/accounts/addresses/
   - Add at least one address
   - Then return to checkout

4. SELECT AN ADDRESS:
   - Click on a non-default address radio button
   - Watch the console - it should stay silent (no logs yet)

5. ENTER COUPON CODE:
   - Type a valid coupon in the field (e.g., "WELCOME10")
   - Click "Apply" button

6. WATCH CONSOLE OUTPUT:
   Expected console logs:
   ---
   Coupon applied successfully, saving form state...
   Selected address element: <input...>
   Saving address ID: [some number]
   Selected payment: cod (or whatever you selected)
   Form state saved, reloading page...
   [PAGE RELOADS]
   Page loaded - checking for saved selections...
   Saved address ID: [same number]
   Found address radio: <input...>
   Address restored successfully
   Restoration complete
   ---

7. CHECK THE RESULT:
   - After reload, is the same address still selected?
   - Is the payment method still selected?
   - Are any notes you typed still there?

COMMON ISSUES & SOLUTIONS:
==========================

ISSUE 1: Console shows "No saved address ID found"
SOLUTION: The address wasn't saved before reload
- Check if you actually selected an address before applying coupon
- Make sure the radio button was checked (should have a blue dot)

ISSUE 2: Console shows "Address radio not found for ID: X"
SOLUTION: The address ID changed between page loads
- This shouldn't happen, but might indicate database issue
- Try clearing browser cache and refreshing

ISSUE 3: Console shows nothing at all
SOLUTION: JavaScript not running
- Make sure JavaScript is enabled in browser
- Check browser console for any JavaScript errors (red text)
- Try hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

ISSUE 4: "Selected address element: null"
SOLUTION: No address was selected when Apply was clicked
- Make sure to click on an address radio button BEFORE applying coupon
- The radio button should show a filled circle/dot when selected

ISSUE 5: Page shows empty form instead of saved addresses
SOLUTION: User has no saved addresses
- Go to http://127.0.0.1:8000/accounts/addresses/
- Click "Add New Address"
- Fill in all required fields and save
- Return to checkout page

TEST CASE TO TRY:
=================
1. Make sure you have at least 2 saved addresses
2. Go to checkout page
3. Select the SECOND address (not the default/first one)
4. Change payment method to "bKash"
5. Type something in Order Notes
6. Apply coupon "WELCOME10"
7. After page reloads:
   ✓ Second address should still be selected
   ✓ Payment method should be bKash
   ✓ Order notes should still have your text
   ✓ Discount should be applied

If all checkmarks pass: ✅ FIX WORKING!
If any fail: ❌ Check console logs and report findings
"""

print(__doc__)
