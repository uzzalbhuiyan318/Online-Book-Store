from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User, Address
from books.models import Book
import uuid


class Order(models.Model):
    """Order Model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order Identification
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Shipping Address
    shipping_full_name = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=20)
    shipping_email = models.EmailField(null=True, blank=True)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, null=True, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='Bangladesh')
    
    # Order Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment Info
    payment_method = models.CharField(max_length=50)  # bkash, nagad, rocket, cod, sslcommerz
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=60)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Notes
    customer_notes = models.TextField(null=True, blank=True)
    customer_notes_bn = models.TextField(null=True, blank=True, verbose_name='Customer Notes (Bangla)')
    admin_notes = models.TextField(null=True, blank=True)
    admin_notes_bn = models.TextField(null=True, blank=True, verbose_name='Admin Notes (Bangla)')

    # Gift order fields
    is_gift = models.BooleanField(default=False, help_text='Whether this order should be treated as a gift')
    gift_from_name = models.CharField(max_length=255, null=True, blank=True)
    gift_from_phone = models.CharField(max_length=20, null=True, blank=True)
    gift_from_alt_phone = models.CharField(max_length=20, null=True, blank=True)
    gift_from_alt_phone = models.CharField(max_length=20, null=True, blank=True)
    gift_message = models.TextField(null=True, blank=True)
    gift_message_bn = models.TextField(null=True, blank=True, verbose_name='Gift Message (Bangla)')
    gift_deliver_date = models.DateField(null=True, blank=True)
    gift_occasion = models.CharField(max_length=50, null=True, blank=True)
    gift_zone = models.CharField(max_length=100, null=True, blank=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4().int)[:6]
        return f"BS{timestamp}{unique_id}"
    
    @property
    def shipping_address(self):
        """Get formatted shipping address"""
        parts = [self.shipping_address_line1]
        if self.shipping_address_line2:
            parts.append(self.shipping_address_line2)
        parts.extend([self.shipping_city, self.shipping_state, self.shipping_postal_code, self.shipping_country])
        return ', '.join(parts)
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    def get_status_display_class(self):
        """Get Bootstrap class for status badge"""
        status_classes = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'info',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')


# Models to drive dynamic gift form options (admin-manageable)
class GiftCity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Gift City'
        verbose_name_plural = 'Gift Cities'

    def __str__(self):
        return self.name


class GiftArea(models.Model):
    city = models.ForeignKey(GiftCity, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Gift Area'
        verbose_name_plural = 'Gift Areas'
        unique_together = ('city', 'name')

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class GiftZone(models.Model):
    area = models.ForeignKey(GiftArea, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Gift Zone'
        verbose_name_plural = 'Gift Zones'
        unique_together = ('area', 'name')

    def __str__(self):
        return f"{self.name} ({self.area.name})"


class GiftOccasion(models.Model):
    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Gift Occasion'
        verbose_name_plural = 'Gift Occasions'

    def __str__(self):
        return self.label



class GiftForm(models.Model):
    """Store submitted gift form data separately so admin can manage gift requests."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='gift_forms')
    is_gift = models.BooleanField(default=True)

    # From
    from_name = models.CharField(max_length=255, null=True, blank=True)
    from_phone = models.CharField(max_length=20, null=True, blank=True)
    from_alt_phone = models.CharField(max_length=20, null=True, blank=True)

    # To / recipient
    to_name = models.CharField(max_length=255, null=True, blank=True)
    to_phone = models.CharField(max_length=20, null=True, blank=True)
    to_email = models.EmailField(null=True, blank=True)
    to_address_line1 = models.CharField(max_length=255, null=True, blank=True)
    to_address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.ForeignKey(GiftCity, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey(GiftArea, on_delete=models.SET_NULL, null=True, blank=True)
    zone = models.ForeignKey(GiftZone, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    occasion = models.ForeignKey(GiftOccasion, on_delete=models.SET_NULL, null=True, blank=True)

    message = models.TextField(null=True, blank=True)
    deliver_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gift Form'
        verbose_name_plural = 'Gift Forms'
        ordering = ['-created_at']

    def __str__(self):
        if self.to_name:
            return f"Gift for {self.to_name} ({self.pk})"
        return f"Gift #{self.pk}"


class OrderItem(models.Model):
    """Order Item Model"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    
    # Store book details at time of order
    book_title = models.CharField(max_length=500)
    book_author = models.CharField(max_length=300)
    book_isbn = models.CharField(max_length=13, null=True, blank=True)
    
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.book_title} x {self.quantity}"


class OrderStatusHistory(models.Model):
    """Order Status Change History"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


class Coupon(models.Model):
    """Coupon Model for discount codes"""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    # Basic Info
    code = models.CharField(max_length=50, unique=True, help_text="Coupon code (case-insensitive)")
    description = models.TextField(blank=True, help_text="Description of the coupon")
    description_bn = models.TextField(blank=True, null=True, help_text="Description of the coupon (Bangla)")
    
    # Discount Settings
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage (0-100) or fixed amount"
    )
    
    # Usage Limits
    max_uses = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of times this coupon can be used (leave empty for unlimited)"
    )
    max_uses_per_user = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Maximum times a single user can use this coupon"
    )
    used_count = models.IntegerField(default=0, help_text="Number of times this coupon has been used")
    
    # Order Requirements
    min_purchase_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount required to use this coupon"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum discount amount (only for percentage discounts)"
    )
    
    # Validity Period
    valid_from = models.DateTimeField(help_text="When the coupon becomes active")
    valid_to = models.DateTimeField(help_text="When the coupon expires")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether the coupon is currently active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"
    
    def save(self, *args, **kwargs):
        # Convert code to uppercase for consistency
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    def get_discount_display(self):
        """Get formatted discount display"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        return f"৳{self.discount_value}"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.max_uses is None or self.used_count < self.max_uses)
        )
    
    def can_be_used_by_user(self, user):
        """Check if coupon can be used by specific user"""
        if not self.is_valid():
            return False, "This coupon is not valid"
        
        # Check user usage count
        usage_count = CouponUsage.objects.filter(coupon=self, user=user).count()
        if usage_count >= self.max_uses_per_user:
            return False, f"You have already used this coupon {self.max_uses_per_user} time(s)"
        
        return True, "Coupon is valid"
    
    def calculate_discount(self, subtotal):
        """Calculate discount amount for given subtotal"""
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / 100
            # Apply max discount limit if set
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            # Fixed amount discount
            discount = self.discount_value
        
        # Discount cannot exceed subtotal
        return min(discount, subtotal)


class CouponUsage(models.Model):
    """Track coupon usage by users"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, related_name='coupon_usage')
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"
