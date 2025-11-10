"""
Setup script for customer support chat system
Run this after migrations to create initial support agents and settings
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from support.models import SupportAgent, ChatSettings, QuickReply

User = get_user_model()

def setup_support():
    print("Setting up Customer Support Chat System...")
    
    # Create or update chat settings
    settings, created = ChatSettings.objects.get_or_create(pk=1)
    if created:
        print("✓ Chat settings created with default values")
    else:
        print("✓ Chat settings already exist")
    
    # Create default quick replies
    quick_replies = [
        {
            'title': 'Shipping Info',
            'title_bn': 'শিপিং তথ্য',
            'content': 'We deliver within 2-5 business days inside Dhaka and 3-7 days outside Dhaka. Shipping is free for orders above 1000 Taka.',
            'content_bn': 'আমরা ঢাকার ভিতরে ২-৫ কার্যদিবস এবং ঢাকার বাইরে ৩-৭ কার্যদিবসের মধ্যে ডেলিভারি দিই। ১০০০ টাকার উপরে অর্ডারের জন্য শিপিং ফ্রি।',
            'category': 'Shipping',
            'order': 1
        },
        {
            'title': 'Payment Methods',
            'title_bn': 'পেমেন্ট পদ্ধতি',
            'content': 'We accept bKash, Nagad, SSLCommerz, and Cash on Delivery. All payments are secure and encrypted.',
            'content_bn': 'আমরা বিকাশ, নগদ, এসএসএলকমার্জ এবং ক্যাশ অন ডেলিভারি গ্রহণ করি। সমস্ত পেমেন্ট সুরক্ষিত এবং এনক্রিপ্টেড।',
            'category': 'Payment',
            'order': 2
        },
        {
            'title': 'Return Policy',
            'title_bn': 'রিটার্ন নীতি',
            'content': 'You can return books within 7 days of delivery if they are damaged or incorrect. Please contact us for the return process.',
            'content_bn': 'ডেলিভারির ৭ দিনের মধ্যে বই ক্ষতিগ্রস্ত বা ভুল হলে ফেরত দিতে পারবেন। রিটার্ন প্রক্রিয়ার জন্য আমাদের সাথে যোগাযোগ করুন।',
            'category': 'Returns',
            'order': 3
        },
        {
            'title': 'Track Order',
            'title_bn': 'অর্ডার ট্র্যাক',
            'content': 'You can track your order from My Orders page. You will also receive SMS updates about your order status.',
            'content_bn': 'আপনি আমার অর্ডার পেজ থেকে আপনার অর্ডার ট্র্যাক করতে পারবেন। আপনি আপনার অর্ডার স্ট্যাটাস সম্পর্কে এসএমএস আপডেটও পাবেন।',
            'category': 'Orders',
            'order': 4
        },
        {
            'title': 'Book Rental',
            'title_bn': 'বই ভাড়া',
            'content': 'We offer book rental services. You can rent books for 7, 14, or 30 days at affordable prices. Visit our Rent Books page to learn more.',
            'content_bn': 'আমরা বই ভাড়া সেবা প্রদান করি। আপনি সাশ্রয়ী মূল্যে ৭, ১৪, বা ৩০ দিনের জন্য বই ভাড়া নিতে পারেন। আরও জানতে আমাদের বই ভাড়া পেজ দেখুন।',
            'category': 'Rentals',
            'order': 5
        }
    ]
    
    for reply_data in quick_replies:
        QuickReply.objects.get_or_create(
            title=reply_data['title'],
            defaults=reply_data
        )
    
    print(f"✓ Created {len(quick_replies)} default quick replies")
    
    # Check for staff/admin users to create support agents
    staff_users = User.objects.filter(is_staff=True)
    
    if staff_users.exists():
        print(f"\nFound {staff_users.count()} staff users. Creating support agents:")
        
        for user in staff_users:
            agent, created = SupportAgent.objects.get_or_create(
                user=user,
                defaults={
                    'display_name': user.full_name or user.email.split('@')[0],
                    'display_name_bn': 'রকমারি',
                    'email': user.email,
                    'is_online': False,
                    'bio': 'Customer Support Representative',
                    'bio_bn': 'গ্রাহক সহায়তা প্রতিনিধি',
                    'order': 1
                }
            )
            
            if created:
                print(f"  ✓ Created support agent for: {user.full_name or user.email}")
            else:
                print(f"  • Support agent already exists for: {user.full_name or user.email}")
    else:
        print("\n⚠ No staff users found. Please create staff users first to add support agents.")
        print("  You can create a staff user with: python manage.py createsuperuser")
    
    print("\n" + "="*60)
    print("Customer Support Chat System Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Go to Admin Panel > Support > Support Agents")
    print("2. Set agents as 'Online' to handle customer chats")
    print("3. Upload agent avatars for better user experience")
    print("4. Customize Chat Settings (colors, messages, etc.)")
    print("5. The chat widget will appear on all pages automatically")
    print("\nAdmin Panel URL: http://localhost:8000/admin/")
    print("="*60)

if __name__ == '__main__':
    setup_support()
