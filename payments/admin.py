from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'transaction_id', 'amount', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__order_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'gateway_response']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'payment_method', 'transaction_id', 'amount', 'status')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
