#!/usr/bin/env python
"""Check and fix chat widget settings"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from support.models import ChatSettings

print("=" * 60)
print("CHAT WIDGET SETTINGS CHECK")
print("=" * 60)

# Get or create settings
settings = ChatSettings.get_settings()

print(f"\nCurrent Settings:")
print(f"  Is Enabled: {settings.is_enabled}")
print(f"  Widget Position: {settings.widget_position}")
print(f"  Primary Color: {settings.primary_color}")
print(f"  Welcome Message (EN): {settings.welcome_message}")
print(f"  Welcome Message (BN): {settings.welcome_message_bn[:50]}...")

if not settings.is_enabled:
    print("\n⚠️  WARNING: Chat widget is DISABLED!")
    response = input("Do you want to ENABLE it? (yes/no): ")
    if response.lower() == 'yes':
        settings.is_enabled = True
        settings.save()
        print("✅ Chat widget has been ENABLED!")
    else:
        print("❌ Chat widget remains disabled.")
else:
    print("\n✅ Chat widget is ENABLED and ready to use!")

print("\n" + "=" * 60)
