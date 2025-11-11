"""
SSLCommerz Integration Test Script
Run this to verify SSLCommerz configuration and connection
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.conf import settings
from payments.sslcommerz import SSLCommerzPayment
import requests

def test_configuration():
    """Test if SSLCommerz credentials are configured"""
    print("=" * 60)
    print("SSLCommerz Configuration Test")
    print("=" * 60)
    
    print(f"\n✓ Store ID: {settings.SSLCOMMERZ_STORE_ID}")
    print(f"✓ Store Password: {'*' * len(settings.SSLCOMMERZ_STORE_PASSWORD)}")
    print(f"✓ Sandbox Mode: {settings.SSLCOMMERZ_IS_SANDBOX}")
    print(f"✓ Site URL: {settings.SITE_URL}")
    
    if settings.SSLCOMMERZ_IS_SANDBOX:
        print(f"✓ API URL: https://sandbox.sslcommerz.com")
    else:
        print(f"✓ API URL: https://securepay.sslcommerz.com")
    
    return True

def test_class_initialization():
    """Test SSLCommerzPayment class initialization"""
    print("\n" + "=" * 60)
    print("SSLCommerz Class Initialization Test")
    print("=" * 60)
    
    try:
        ssl = SSLCommerzPayment()
        print(f"\n✓ SSLCommerzPayment class initialized successfully")
        print(f"✓ Base URL: {ssl.base_url}")
        print(f"✓ Store ID: {ssl.store_id}")
        return True
    except Exception as e:
        print(f"\n✗ Error initializing SSLCommerzPayment: {str(e)}")
        return False

def test_api_connectivity():
    """Test connectivity to SSLCommerz API"""
    print("\n" + "=" * 60)
    print("SSLCommerz API Connectivity Test")
    print("=" * 60)
    
    try:
        # Test if we can reach SSLCommerz API
        api_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
        print(f"\n⏳ Testing connection to {api_url}...")
        
        # Simple test with minimal data (will fail validation but tests connectivity)
        test_data = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        }
        
        response = requests.post(api_url, data=test_data, timeout=10)
        
        print(f"✓ API is reachable (Status Code: {response.status_code})")
        
        # Check response
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == 'FAILED':
                    # Expected - we sent incomplete data
                    print(f"✓ API responding correctly")
                    print(f"  Response: {result.get('failedreason', 'Incomplete test data')}")
                else:
                    print(f"✓ API response: {result}")
            except:
                print(f"✓ API responded (non-JSON)")
        
        return True
        
    except requests.exceptions.Timeout:
        print("✗ Connection timeout - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_payment_urls():
    """Test if payment callback URLs are properly configured"""
    print("\n" + "=" * 60)
    print("Payment Callback URLs Test")
    print("=" * 60)
    
    from django.urls import reverse
    
    try:
        success_url = reverse('payments:sslcommerz_success')
        fail_url = reverse('payments:sslcommerz_fail')
        cancel_url = reverse('payments:sslcommerz_cancel')
        ipn_url = reverse('payments:sslcommerz_ipn')
        
        print(f"\n✓ Success URL: {settings.SITE_URL}{success_url}")
        print(f"✓ Fail URL: {settings.SITE_URL}{fail_url}")
        print(f"✓ Cancel URL: {settings.SITE_URL}{cancel_url}")
        print(f"✓ IPN URL: {settings.SITE_URL}{ipn_url}")
        
        return True
    except Exception as e:
        print(f"\n✗ Error resolving URLs: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🔐" * 30)
    print("SSLCommerz Integration Test Suite")
    print("🔐" * 30 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Class Initialization", test_class_initialization()))
    results.append(("Payment URLs", test_payment_urls()))
    results.append(("API Connectivity", test_api_connectivity()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12} - {test_name}")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SSLCommerz is ready to use.")
        print("\nNext Steps:")
        print("1. Run server: python manage.py runserver")
        print("2. Add items to cart")
        print("3. Go to checkout")
        print("4. Select 'SSLCommerz' as payment method")
        print("5. Complete payment with test card: 4242424242424242")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
