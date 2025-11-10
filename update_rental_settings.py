# Update existing rental settings to new max active rentals limit

from rentals.models import RentalSettings

def update_settings():
    settings = RentalSettings.get_settings()
    old_value = settings.max_active_rentals_per_user
    settings.max_active_rentals_per_user = 3
    settings.save()
    
    print(f"Updated max_active_rentals_per_user: {old_value} -> 3")
    print(f"Settings updated successfully!")
    print(f"\nCurrent Settings:")
    print(f"  - Security Deposit: {settings.security_deposit_percentage}%")
    print(f"  - Daily Late Fee: {settings.daily_late_fee}")
    print(f"  - Max Active Rentals Per User: {settings.max_active_rentals_per_user} <- NEW")
    print(f"  - Max Renewals: {settings.max_renewals}")

if __name__ == '__main__':
    update_settings()

