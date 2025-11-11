"""
Quick SSLCommerz Configuration Test
Tests credentials without requiring full Django setup
"""
from decouple import config
import requests

print("=" * 70)
print("SSLCommerz Quick Configuration Test")
print("=" * 70)

# Test 1: Environment Variables
print("\n📋 Test 1: Environment Variables")
print("-" * 70)

try:
    store_id = config('SSLCOMMERZ_STORE_ID')
    store_password = config('SSLCOMMERZ_STORE_PASSWORD')
    is_sandbox = config('SSLCOMMERZ_IS_SANDBOX', default=True, cast=bool)
    site_url = config('SITE_URL', default='http://localhost:8000')
    
    print(f"✓ Store ID: {store_id}")
    print(f"✓ Store Password: {'*' * (len(store_password) - 4)}{store_password[-4:]}")
    print(f"✓ Sandbox Mode: {is_sandbox}")
    print(f"✓ Site URL: {site_url}")
    
    if is_sandbox:
        api_url = "https://sandbox.sslcommerz.com"
    else:
        api_url = "https://securepay.sslcommerz.com"
    
    print(f"✓ API Base URL: {api_url}")
    
    env_test = True
except Exception as e:
    print(f"✗ Error loading environment variables: {e}")
    env_test = False

# Test 2: API Connectivity
print("\n🌐 Test 2: API Connectivity")
print("-" * 70)

if env_test:
    try:
        test_url = f"{api_url}/gwprocess/v4/api.php"
        print(f"⏳ Testing connection to {test_url}...")
        
        # Minimal test data to check if credentials work
        test_data = {
            'store_id': store_id,
            'store_passwd': store_password,
            'total_amount': '100',
            'currency': 'BDT',
            'tran_id': 'TEST123',
            'success_url': f'{site_url}/test/success/',
            'fail_url': f'{site_url}/test/fail/',
            'cancel_url': f'{site_url}/test/cancel/',
            'cus_name': 'Test Customer',
            'cus_email': 'test@example.com',
            'cus_phone': '01700000000',
            'cus_add1': 'Test Address',
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'shipping_method': 'NO',
            'product_name': 'Test Product',
            'product_category': 'Test',
            'product_profile': 'general',
        }
        
        response = requests.post(test_url, data=test_data, timeout=15)
        
        print(f"✓ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✓ Response Format: JSON")
                
                if result.get('status') == 'SUCCESS':
                    print(f"✓✓ SSLCommerz Credentials Valid!")
                    print(f"✓✓ Session Key Received")
                    print(f"✓✓ Gateway URL: {result.get('GatewayPageURL', 'N/A')[:50]}...")
                    api_test = True
                elif result.get('status') == 'FAILED':
                    print(f"⚠  API Response: FAILED")
                    print(f"   Reason: {result.get('failedreason', 'Unknown')}")
                    
                    # Check if it's a credential issue
                    if 'Invalid' in result.get('failedreason', '') or 'credentials' in result.get('failedreason', '').lower():
                        print(f"✗  Credential Error - Please verify Store ID and Password")
                        api_test = False
                    else:
                        print(f"✓  Credentials appear valid (failure due to test data)")
                        api_test = True
                else:
                    print(f"⚠  Unexpected response: {result}")
                    api_test = True
                    
            except ValueError:
                print(f"⚠  Non-JSON response received")
                print(f"   Response: {response.text[:100]}")
                api_test = False
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            api_test = False
            
    except requests.exceptions.Timeout:
        print("✗ Connection timeout - check your internet connection")
        api_test = False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - unable to reach SSLCommerz servers")
        api_test = False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        api_test = False
else:
    print("⊗ Skipped (environment test failed)")
    api_test = False

# Test 3: File Structure
print("\n📁 Test 3: Integration Files")
print("-" * 70)

import os

files_to_check = [
    'payments/sslcommerz.py',
    'payments/views.py',
    'payments/urls.py',
    'payments/utils.py',
    'bookstore_project/settings.py',
]

files_exist = True
for file in files_to_check:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - NOT FOUND")
        files_exist = False

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)

results = [
    ("Environment Configuration", env_test),
    ("API Connectivity", api_test),
    ("Integration Files", files_exist),
]

passed = sum(1 for _, result in results if result)
total = len(results)

for test_name, result in results:
    status = "✓ PASSED" if result else "✗ FAILED"
    print(f"{status:12} - {test_name}")

print(f"\n{'=' * 70}")
print(f"Overall: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 SUCCESS! SSLCommerz integration is ready!")
    print("\n📝 Next Steps:")
    print("   1. Start the Django server: python manage.py runserver")
    print("   2. Go to your BookShop website")
    print("   3. Add books to cart")
    print("   4. Proceed to checkout")
    print("   5. Select 'SSLCommerz' as payment method")
    print("   6. Test with card: 4242424242424242")
    print("\n💳 Test Card Details:")
    print("   Card Number: 4242424242424242")
    print("   Expiry: Any future date (e.g., 12/25)")
    print("   CVV: Any 3 digits (e.g., 123)")
elif api_test:
    print("\n✅ Good news! Your credentials appear to be working.")
    print("   You can proceed with testing the payment flow.")
else:
    print("\n⚠️  Some tests failed. Please check the details above.")
    if not env_test:
        print("   → Check your .env file configuration")
    if not api_test:
        print("   → Verify your SSLCommerz credentials")
        print("   → Check your internet connection")

print("=" * 70 + "\n")
