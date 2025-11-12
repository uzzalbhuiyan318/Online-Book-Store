"""
Quick Email Test - Real SMTP Email Sending
Run this to verify real emails are being sent
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_real_email():
    print("=" * 80)
    print("REAL EMAIL TEST - SMTP MODE")
    print("=" * 80)
    print()
    
    # Show current settings
    print("📧 Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   Use TLS: {settings.EMAIL_USE_TLS}")
    print()
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("⚠️  WARNING: Still in console mode!")
        print("   To send real emails, set USE_CONSOLE_EMAIL=False in .env")
        return False
    
    print("✅ SMTP mode is active - attempting to send real email...")
    print()
    
    # Get recipient email
    recipient = input("Enter recipient email (or press Enter for your email): ").strip()
    if not recipient:
        recipient = settings.EMAIL_HOST_USER
    
    print(f"   Sending to: {recipient}")
    print()
    
    try:
        send_mail(
            subject='🎉 Test Email from BookStore',
            message='This is a test email to verify SMTP configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("✅ SUCCESS! Email sent successfully!")
        print(f"   Check inbox: {recipient}")
        print()
        print("🎯 Next Steps:")
        print("   1. Check the recipient's email inbox")
        print("   2. Check spam folder if not in inbox")
        print("   3. Once confirmed, place a test order on your site")
        print("   4. Customer will receive order confirmation email automatically")
        return True
        
    except Exception as e:
        print(f"❌ FAILED! Error sending email:")
        print(f"   {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check your Gmail App Password is correct")
        print("   2. Ensure Less Secure App Access is enabled (if using regular password)")
        print("   3. Try generating a new App Password at:")
        print("      https://myaccount.google.com/apppasswords")
        print("   4. Check your internet connection")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_real_email()
