"""
Quick Setup Script for Book Rental System
Run this after migrations are complete
"""

from rentals.models import RentalPlan, RentalSettings

def create_rental_plans():
    """Create default rental plans"""
    
    plans = [
        {
            'name': 'Weekly Rental',
            'days': 7,
            'price_percentage': 10.00,
            'order': 1
        },
        {
            'name': 'Bi-Weekly Rental',
            'days': 14,
            'price_percentage': 15.00,
            'order': 2
        },
        {
            'name': 'Monthly Rental',
            'days': 30,
            'price_percentage': 25.00,
            'order': 3
        },
        {
            'name': '2-Month Rental',
            'days': 60,
            'price_percentage': 40.00,
            'order': 4
        },
    ]
    
    created_count = 0
    for plan_data in plans:
        plan, created = RentalPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults=plan_data
        )
        if created:
            created_count += 1
            print(f"✓ Created: {plan.name} - {plan.days} days ({plan.price_percentage}%)")
        else:
            print(f"→ Already exists: {plan.name}")
    
    print(f"\n{created_count} new rental plans created!")
    return created_count


def initialize_settings():
    """Initialize rental settings with default values"""
    settings = RentalSettings.get_settings()
    print("\n✓ Rental Settings Initialized:")
    print(f"  - Security Deposit: {settings.security_deposit_percentage}%")
    print(f"  - Daily Late Fee: ৳{settings.daily_late_fee}")
    print(f"  - Max Active Rentals Per User: {settings.max_active_rentals_per_user}")
    print(f"  - Max Renewals: {settings.max_renewals}")
    print(f"  - Due Soon Notification: {settings.due_soon_days} days before")
    print(f"  - Min Stock for Rental: {settings.min_stock_for_rental}")
    print(f"  - Notifications Enabled: {settings.enable_notifications}")
    
    return settings


def main():
    print("=" * 60)
    print("Book Rental System - Quick Setup")
    print("=" * 60)
    print()
    
    try:
        # Create rental plans
        print("Creating Rental Plans...")
        print("-" * 60)
        create_rental_plans()
        
        print()
        
        # Initialize settings
        print("Initializing Rental Settings...")
        print("-" * 60)
        initialize_settings()
        
        print()
        print("=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Go to /admin/rentals/ to manage rental system")
        print("2. Adjust rental plans and settings as needed")
        print("3. Add 'Rent This Book' button to book detail pages")
        print("4. Test the rental flow")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        print("Make sure you have run migrations first:")
        print("  python manage.py makemigrations rentals")
        print("  python manage.py migrate")


if __name__ == '__main__':
    # For Django shell
    main()
else:
    # When imported in Django shell
    print("Run: exec(open('setup_rentals.py').read())")
