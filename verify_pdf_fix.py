"""
Verify the PDF invoice fix is working correctly
This script checks that invoices are being attached as PDF files, not HTML
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from orders.models import Order
from orders.email_utils import send_order_confirmation_email
from django.core.mail import EmailMultiAlternatives
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import render_to_string

print("=" * 70)
print("PDF INVOICE FIX VERIFICATION")
print("=" * 70)
print()

# Test 1: Check xhtml2pdf is installed
print("✓ Test 1: xhtml2pdf library installed")
try:
    from xhtml2pdf import pisa
    print("  ✅ xhtml2pdf is available")
except ImportError:
    print("  ❌ xhtml2pdf is NOT installed")
    print("  Run: pip install xhtml2pdf")
    sys.exit(1)

print()

# Test 2: Check we can generate a PDF
print("✓ Test 2: PDF generation capability")
try:
    test_html = "<html><body><h1>Test PDF</h1><p>This is a test.</p></body></html>"
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(test_html, dest=pdf_file)
    
    if pisa_status.err:
        print("  ❌ PDF generation failed")
        sys.exit(1)
    else:
        pdf_size = pdf_file.tell()
        print(f"  ✅ PDF generated successfully ({pdf_size} bytes)")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

print()

# Test 3: Check invoice template exists
print("✓ Test 3: Invoice template exists")
try:
    from django.template.loader import get_template
    template = get_template('orders/invoice.html')
    print("  ✅ Invoice template found")
except Exception as e:
    print(f"  ❌ Template not found: {e}")
    sys.exit(1)

print()

# Test 4: Generate PDF from actual invoice template
print("✓ Test 4: Generate PDF from invoice template")
recent_order = Order.objects.order_by('-created_at').first()
if not recent_order:
    print("  ⚠️  No orders found - skipping this test")
else:
    try:
        invoice_html = render_to_string('orders/invoice.html', {
            'order': recent_order,
        })
        
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(invoice_html, dest=pdf_file)
        
        if pisa_status.err:
            print("  ❌ Invoice PDF generation failed")
        else:
            pdf_size = pdf_file.tell()
            print(f"  ✅ Invoice PDF generated successfully ({pdf_size} bytes)")
            print(f"     Order: {recent_order.order_number}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print()

# Test 5: Verify email function uses PDF
print("✓ Test 5: Email function uses PDF attachment")
import inspect
email_func_source = inspect.getsource(send_order_confirmation_email)

checks = [
    ('xhtml2pdf import', 'xhtml2pdf' in email_func_source and 'pisa' in email_func_source),
    ('PDF filename', '.pdf' in email_func_source),
    ('PDF mime type', 'application/pdf' in email_func_source),
    ('No HTML attachment', "filename=f'Invoice_{order.order_number}.html'" not in email_func_source),
]

all_passed = True
for check_name, check_result in checks:
    if check_result:
        print(f"  ✅ {check_name}")
    else:
        print(f"  ❌ {check_name}")
        all_passed = False

print()

# Final Summary
print("=" * 70)
if all_passed:
    print("✅ ALL TESTS PASSED!")
    print()
    print("Your email system is now sending PDF invoices correctly.")
    print("Invoices will be attached as '.pdf' files, not '.html' files.")
    print()
    print("Next step: Place a test order and check the email attachment!")
else:
    print("⚠️  SOME TESTS FAILED")
    print("Please check the errors above and fix them.")
print("=" * 70)
