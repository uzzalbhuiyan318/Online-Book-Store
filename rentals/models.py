from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from books.models import Book
from datetime import timedelta
import uuid


class RentalPlan(models.Model):
    """Rental Plan Model - Define different rental durations and pricing"""
    
    name = models.CharField(max_length=100, verbose_name='Plan Name')
    days = models.IntegerField(verbose_name='Duration (Days)', validators=[MinValueValidator(1)])
    price_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Price Percentage of Book Price',
        help_text='Percentage of book price to charge (e.g., 10 for 10%)',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rental Plan'
        verbose_name_plural = 'Rental Plans'
        ordering = ['order', 'days']
    
    def __str__(self):
        return f"{self.name} - {self.days} days ({self.price_percentage}%)"
    
    def calculate_rental_price(self, book_price):
        """Calculate rental price based on book price"""
        return (book_price * self.price_percentage) / 100


class BookRental(models.Model):
    """Book Rental Model - Main rental transaction"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    # Rental Identification
    rental_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='rentals')
    rental_plan = models.ForeignKey('RentalPlan', on_delete=models.SET_NULL, null=True)
    
    # Rental Details
    rental_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Rental Price')
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Security Deposit')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total Amount')
    
    # Dates
    rental_date = models.DateTimeField(auto_now_add=True, verbose_name='Rental Date')
    start_date = models.DateTimeField(null=True, blank=True, verbose_name='Start Date')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Due Date')
    return_date = models.DateTimeField(null=True, blank=True, verbose_name='Actual Return Date')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment Info
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Late Fee
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Late Fee')
    late_days = models.IntegerField(default=0, verbose_name='Days Late')
    
    # Renewal
    renewal_count = models.IntegerField(default=0, verbose_name='Times Renewed')
    can_renew = models.BooleanField(default=True, verbose_name='Can Renew')
    
    # Notes
    customer_notes = models.TextField(null=True, blank=True, verbose_name='Customer Notes')
    admin_notes = models.TextField(null=True, blank=True, verbose_name='Admin Notes')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Book Rental'
        verbose_name_plural = 'Book Rentals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.rental_number} - {self.user.email} - {self.book.title}"
    
    def save(self, *args, **kwargs):
        if not self.rental_number:
            self.rental_number = self.generate_rental_number()
        
        # Calculate total amount
        if not self.total_amount or self.total_amount == 0:
            self.total_amount = self.rental_price + self.security_deposit
        
        # Set start date and due date when status becomes active
        if self.status == 'active' and not self.start_date:
            self.start_date = timezone.now()
            if self.rental_plan:
                self.due_date = self.start_date + timedelta(days=self.rental_plan.days)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_rental_number():
        """Generate unique rental number"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4().int)[:6]
        return f"RNT{timestamp}{unique_id}"
    
    @property
    def is_overdue(self):
        """Check if rental is overdue"""
        if self.status == 'active' and self.due_date:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        if self.status == 'active' and self.due_date:
            delta = self.due_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    @property
    def overdue_days(self):
        """Calculate overdue days"""
        if self.is_overdue:
            delta = timezone.now() - self.due_date
            return delta.days
        return 0
    
    def calculate_late_fee(self, daily_late_fee=10):
        """Calculate late fee based on overdue days"""
        if self.is_overdue:
            self.late_days = self.overdue_days
            self.late_fee = self.late_days * daily_late_fee
            self.save()
        return self.late_fee
    
    def mark_as_returned(self):
        """Mark rental as returned"""
        self.return_date = timezone.now()
        self.status = 'returned'
        
        # Calculate late fee if overdue
        if self.is_overdue:
            self.calculate_late_fee()
        
        self.save()
        
        # Return book to stock
        self.book.stock += 1
        self.book.save()
    
    def renew(self, additional_days=None):
        """Renew rental for additional days"""
        if not self.can_renew:
            return False, "This rental cannot be renewed"
        
        if self.status != 'active':
            return False, "Only active rentals can be renewed"
        
        # Use rental plan days if not specified
        if additional_days is None and self.rental_plan:
            additional_days = self.rental_plan.days
        
        if additional_days:
            self.due_date = self.due_date + timedelta(days=additional_days)
            self.renewal_count += 1
            
            # Check renewal limit
            settings = RentalSettings.get_settings()
            if self.renewal_count >= settings.max_renewals:
                self.can_renew = False
            
            self.save()
            return True, f"Rental renewed for {additional_days} days"
        
        return False, "Invalid renewal period"


class RentalStatusHistory(models.Model):
    """Rental Status Change History"""
    
    rental = models.ForeignKey(BookRental, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rental Status History'
        verbose_name_plural = 'Rental Status Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rental.rental_number} - {self.status}"


class RentalFeedback(models.Model):
    """Rental Feedback Model - User feedback after returning book"""
    
    rental = models.OneToOneField(BookRental, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_feedbacks')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='rental_feedbacks')
    
    # Ratings
    book_condition_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Book Condition Rating (1-5)',
        help_text='Rate the condition of the book you received'
    )
    service_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Service Rating (1-5)',
        help_text='Rate our rental service'
    )
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Overall Rating (1-5)'
    )
    
    # Comments
    comment = models.TextField(verbose_name='Your Feedback', blank=True)
    
    # Admin Response
    admin_response = models.TextField(null=True, blank=True, verbose_name='Admin Response')
    
    # Status
    is_approved = models.BooleanField(default=False, verbose_name='Approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rental Feedback'
        verbose_name_plural = 'Rental Feedbacks'
        ordering = ['-created_at']
    
    def __str__(self):
        rating = self.overall_rating if self.overall_rating else 'N/A'
        return f"Feedback for {self.rental.rental_number} - {rating}★"
    
    @property
    def average_rating(self):
        """Calculate average of all ratings"""
        # Handle None values (when feedback is being created)
        if None in [self.book_condition_rating, self.service_rating, self.overall_rating]:
            return 0
        return round((self.book_condition_rating + self.service_rating + self.overall_rating) / 3, 1)


class RentalNotification(models.Model):
    """Rental Notification Model - Track notifications sent to users"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('rental_confirmed', 'Rental Confirmed'),
        ('rental_active', 'Rental Active'),
        ('due_soon', 'Due Soon (3 days)'),
        ('due_tomorrow', 'Due Tomorrow'),
        ('overdue', 'Overdue'),
        ('returned', 'Returned'),
        ('renewal_confirmed', 'Renewal Confirmed'),
        ('feedback_request', 'Feedback Request'),
    ]
    
    rental = models.ForeignKey(BookRental, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Message
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False, verbose_name='Read')
    is_sent = models.BooleanField(default=False, verbose_name='Sent')
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rental Notification'
        verbose_name_plural = 'Rental Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['rental', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_notification_type_display()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()


class RentalSettings(models.Model):
    """Global Rental Settings"""
    
    # Pricing
    security_deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name='Security Deposit Percentage',
        help_text='Percentage of book price to hold as security deposit'
    )
    daily_late_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10,
        verbose_name='Daily Late Fee (BDT)',
        help_text='Amount charged per day for overdue rentals'
    )
    
    # Limits
    max_active_rentals_per_user = models.IntegerField(
        default=3,
        verbose_name='Max Active Rentals Per User',
        help_text='Maximum number of active rentals a user can have at the same time'
    )
    max_renewals = models.IntegerField(
        default=3,
        verbose_name='Max Renewals',
        help_text='Maximum number of times a rental can be renewed'
    )
    
    # Notifications
    enable_notifications = models.BooleanField(default=True, verbose_name='Enable Notifications')
    due_soon_days = models.IntegerField(default=3, verbose_name='Due Soon Notification (Days)')
    
    # Rental Availability
    min_stock_for_rental = models.IntegerField(
        default=1,
        verbose_name='Minimum Stock for Rental',
        help_text='Minimum stock quantity required to allow rental'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rental Settings'
        verbose_name_plural = 'Rental Settings'
    
    def __str__(self):
        return 'Rental Settings'
    
    @classmethod
    def get_settings(cls):
        """Get or create rental settings singleton"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
