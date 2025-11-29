from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db import models
from django import forms
from .models import Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage
from .models import GiftCity, GiftArea, GiftZone, GiftOccasion
from .models import GiftForm
from django.http import HttpResponse
import csv
import logging
from .email_utils import send_order_confirmation_email

logger = logging.getLogger(__name__)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['book_title', 'book_author', 'quantity', 'price', 'subtotal']
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'notes', 'changed_by', 'created_at']
    can_delete = False


class GiftFormInline(admin.StackedInline):
    model = GiftForm
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fk_name = 'order'
    can_delete = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'is_gift', 'payment_method', 'total', 'shipping_full_name', 'shipping_phone', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'is_gift', 'created_at']
    search_fields = ['order_number', 'user__email', 'transaction_id', 'shipping_phone', 'shipping_full_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline, GiftFormInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_full_name', 'shipping_phone', 'shipping_email',
                'shipping_address_line1', 'shipping_address_line2',
                'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country'
            )
        }),
        ('Payment', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'discount', 'total')
        }),
        ('Notes & Tracking', {
            'fields': ('customer_notes', 'admin_notes', 'tracking_number')
        }),
        ('Gift Info', {
            'fields': ('is_gift', 'gift_from_name', 'gift_from_phone', 'gift_from_alt_phone', 'gift_message', 'gift_occasion', 'gift_zone', 'gift_deliver_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change:  # If updating existing order
            # Check if status changed
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=obj,
                    status=obj.status,
                    changed_by=request.user
                )
                
                # Update timestamps
                if obj.status == 'confirmed' and not obj.confirmed_at:
                    obj.confirmed_at = timezone.now()
                elif obj.status == 'shipped' and not obj.shipped_at:
                    obj.shipped_at = timezone.now()
                elif obj.status == 'delivered' and not obj.delivered_at:
                    obj.delivered_at = timezone.now()
        
        super().save_model(request, obj, form, change)

    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered', 'mark_cancelled', 'export_as_csv', 'send_confirmation_email']

    def mark_confirmed(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != 'confirmed':
                order.status = 'confirmed'
                order.confirmed_at = timezone.now()
                order.save()
                OrderStatusHistory.objects.create(order=order, status='confirmed', changed_by=request.user)
                count += 1
        self.message_user(request, f"Marked {count} order(s) as confirmed")
    mark_confirmed.short_description = 'Mark selected orders as confirmed'

    def mark_shipped(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != 'shipped':
                order.status = 'shipped'
                order.shipped_at = timezone.now()
                order.save()
                OrderStatusHistory.objects.create(order=order, status='shipped', changed_by=request.user)
                count += 1
        self.message_user(request, f"Marked {count} order(s) as shipped")
    mark_shipped.short_description = 'Mark selected orders as shipped'

    def mark_delivered(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != 'delivered':
                order.status = 'delivered'
                order.delivered_at = timezone.now()
                order.save()
                OrderStatusHistory.objects.create(order=order, status='delivered', changed_by=request.user)
                count += 1
        self.message_user(request, f"Marked {count} order(s) as delivered")
    mark_delivered.short_description = 'Mark selected orders as delivered'

    def mark_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != 'cancelled':
                order.status = 'cancelled'
                order.save()
                OrderStatusHistory.objects.create(order=order, status='cancelled', changed_by=request.user)
                count += 1
        self.message_user(request, f"Marked {count} order(s) as cancelled")
    mark_cancelled.short_description = 'Mark selected orders as cancelled'

    def export_as_csv(self, request, queryset):
        """Export selected orders as CSV download."""
        field_names = ['order_number', 'user_email', 'status', 'payment_status', 'payment_method', 'total', 'shipping_full_name', 'shipping_phone', 'created_at']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=orders_export.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([
                obj.order_number,
                obj.user.email if obj.user else '',
                obj.status,
                obj.payment_status,
                obj.payment_method,
                str(obj.total),
                obj.shipping_full_name,
                obj.shipping_phone,
                obj.created_at,
            ])
        return response
    export_as_csv.short_description = 'Export selected orders as CSV'

    def send_confirmation_email(self, request, queryset):
        sent = 0
        for order in queryset:
            try:
                if send_order_confirmation_email(order):
                    sent += 1
            except Exception:
                logger.exception('Failed to send confirmation email for order %s', order.order_number)
        self.message_user(request, f'Sent confirmation email for {sent} order(s)')
    send_confirmation_email.short_description = 'Send order confirmation email for selected orders'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'book_title', 'quantity', 'price', 'subtotal']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'book_title', 'book_author']
    readonly_fields = ['created_at']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['created_at']


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ['user', 'order', 'used_at']
    can_delete = False


class CouponAdminForm(forms.ModelForm):
    """Custom form for Coupon admin with better datetime widgets"""
    
    valid_from = forms.SplitDateTimeField(
        widget=admin.widgets.AdminSplitDateTime(),
        help_text="When the coupon becomes active"
    )
    valid_to = forms.SplitDateTimeField(
        widget=admin.widgets.AdminSplitDateTime(),
        help_text="When the coupon expires"
    )
    
    class Meta:
        model = Coupon
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        # Validate that valid_to is after valid_from
        if valid_from and valid_to:
            if valid_to <= valid_from:
                raise forms.ValidationError("End date must be after start date.")
        
        # Validate discount value based on type
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        
        if discount_type == 'percentage' and discount_value:
            if discount_value > 100:
                raise forms.ValidationError("Percentage discount cannot exceed 100%.")
            if discount_value <= 0:
                raise forms.ValidationError("Discount value must be greater than 0.")
        
        return cleaned_data


class CouponValidityFilter(admin.SimpleListFilter):
    """Filter coupons by validity status"""
    title = 'validity status'
    parameter_name = 'validity'
    
    def lookups(self, request, model_admin):
        return (
            ('valid', 'Valid & Active'),
            ('expired', 'Expired'),
            ('upcoming', 'Not Yet Active'),
            ('inactive', 'Inactive'),
            ('limit_reached', 'Limit Reached'),
        )
    
    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'valid':
            return queryset.filter(
                is_active=True,
                valid_from__lte=now,
                valid_to__gte=now
            ).exclude(
                used_count__gte=models.F('max_uses')
            )
        elif self.value() == 'expired':
            return queryset.filter(valid_to__lt=now)
        elif self.value() == 'upcoming':
            return queryset.filter(valid_from__gt=now)
        elif self.value() == 'inactive':
            return queryset.filter(is_active=False)
        elif self.value() == 'limit_reached':
            return queryset.filter(used_count__gte=models.F('max_uses')).exclude(max_uses__isnull=True)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    form = CouponAdminForm
    list_display = ['code', 'discount_display', 'validity_status', 'is_active', 'valid_from', 'valid_to', 'usage_display', 'max_uses']
    list_filter = [CouponValidityFilter, 'discount_type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at', 'updated_at', 'validity_status']
    inlines = [CouponUsageInline]
    actions = ['activate_coupons', 'deactivate_coupons']
    ordering = ['-created_at']
    
    class Media:
        js = ('admin/js/calendar.js', 'admin/js/admin/DateTimeShortcuts.js')
        css = {
            'all': ('admin/css/widgets.css',)
        }
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'max_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'max_uses_per_user', 'used_count')
        }),
        ('Order Requirements', {
            'fields': ('min_purchase_amount',)
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure code is uppercase
        obj.code = obj.code.upper()
        super().save_model(request, obj, form, change)
    
    def discount_display(self, obj):
        """Display formatted discount"""
        return obj.get_discount_display()
    discount_display.short_description = 'Discount'
    
    def validity_status(self, obj):
        """Display current validity status with color"""
        if obj.is_valid():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        
        now = timezone.now()
        if now < obj.valid_from:
            return format_html(
                '<span style="color: orange;">⏳ Not yet active</span>'
            )
        elif now > obj.valid_to:
            return format_html(
                '<span style="color: red;">✗ Expired</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="color: gray;">✗ Inactive</span>'
            )
        elif obj.max_uses and obj.used_count >= obj.max_uses:
            return format_html(
                '<span style="color: red;">✗ Limit reached</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Invalid</span>'
        )
    validity_status.short_description = 'Status'
    
    def usage_display(self, obj):
        """Display usage count with visual indicator"""
        if obj.max_uses:
            percentage = (obj.used_count / obj.max_uses) * 100
            color = 'green' if percentage < 50 else ('orange' if percentage < 80 else 'red')
            return format_html(
                '<span style="color: {};">{}/{}</span>',
                color, obj.used_count, obj.max_uses
            )
        return f"{obj.used_count}/∞"
    usage_display.short_description = 'Used'
    
    def activate_coupons(self, request, queryset):
        """Activate selected coupons"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} coupon(s) activated successfully.")
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        """Deactivate selected coupons"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} coupon(s) deactivated successfully.")
    deactivate_coupons.short_description = "Deactivate selected coupons"


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'used_at']
    list_filter = ['used_at', 'coupon']
    search_fields = ['coupon__code', 'user__email', 'order__order_number']
    readonly_fields = ['used_at']


@admin.register(GiftCity)
class GiftCityAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(GiftArea)
class GiftAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']
    list_filter = ['city']
    search_fields = ['name', 'city__name']


@admin.register(GiftZone)
class GiftZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'area']
    list_filter = ['area__city']
    search_fields = ['name', 'area__name']


@admin.register(GiftOccasion)
class GiftOccasionAdmin(admin.ModelAdmin):
    list_display = ['key', 'label']
    search_fields = ['key', 'label']


@admin.register(GiftForm)
class GiftFormAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'to_name', 'to_phone', 'city', 'area', 'zone', 'occasion', 'status', 'created_at']
    list_filter = ['status', 'city', 'area', 'occasion', 'created_at']
    search_fields = ['to_name', 'to_phone', 'from_name', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Order Link', {'fields': ('order',)}),
        ('Sender', {'fields': ('from_name', 'from_phone', 'from_alt_phone')}),
        ('Recipient', {'fields': (
            'to_name', 'to_phone', 'to_email', 'to_address_line1', 'to_address_line2',
            'city', 'area', 'zone', 'postal_code', 'state', 'occasion'
        )}),
        ('Message & Delivery', {'fields': ('message', 'deliver_date')}),
        ('Admin', {'fields': ('status', 'created_at', 'updated_at')}),
    )

    actions = ['mark_processed', 'mark_cancelled']

    def mark_processed(self, request, queryset):
        updated = queryset.update(status='processed')
        self.message_user(request, f"Marked {updated} gift form(s) as processed")
    mark_processed.short_description = 'Mark selected as processed'

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"Marked {updated} gift form(s) as cancelled")
    mark_cancelled.short_description = 'Mark selected as cancelled'
