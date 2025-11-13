from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['get_reference', 'payment_method', 'transaction_id', 'amount', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__order_number', 'rental__rental_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'gateway_response']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'rental', 'payment_method', 'transaction_id', 'amount', 'status')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_reference(self, obj):
        """Display either order number or rental number"""
        if obj.order:
            return f"Order: {obj.order.order_number}"
        elif obj.rental:
            return f"Rental: {obj.rental.rental_number}"
        return "N/A"
    get_reference.short_description = 'Reference'
