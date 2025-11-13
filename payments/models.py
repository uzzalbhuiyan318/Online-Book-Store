from django.db import models
from orders.models import Order


class Payment(models.Model):
    """Payment Model - supports both orders and rentals"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Either order or rental must be set (but not both)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    rental = models.ForeignKey('rentals.BookRental', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    payment_method = models.CharField(max_length=50)  # bkash, nagad, rocket, sslcommerz, cod
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Gateway Response
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.order:
            return f"{self.order.order_number} - {self.payment_method} - {self.status}"
        elif self.rental:
            return f"{self.rental.rental_number} - {self.payment_method} - {self.status}"
        else:
            return f"{self.transaction_id} - {self.payment_method} - {self.status}"
