from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    RentalPlan, BookRental, RentalStatusHistory,
    RentalFeedback, RentalNotification, RentalSettings
)


@admin.register(RentalPlan)
class RentalPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'days', 'rental_price_display', 'book_count', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'days']
    filter_horizontal = ['books']  # Better UI for ManyToMany field
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'name_bn', 'description', 'description_bn', 'days')
        }),
        ('Available Books', {
            'fields': ('books',),
            'description': 'Select which books can be rented with this plan. Only selected books will show this plan as an option.'
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    def rental_price_display(self, obj):
        """Display calculated rental price"""
        price = obj.calculate_rental_price()
        return format_html('<strong>৳{}</strong>', price)
    rental_price_display.short_description = 'Rental Price'
    
    def book_count(self, obj):
        """Display number of books in this plan"""
        count = obj.books.count()
        if count == 0:
            return format_html('<span style="color: red;">⚠️ 0 books</span>')
        return format_html('<span style="color: green;">✓ {} book(s)</span>', count)
    book_count.short_description = 'Books'


class RentalStatusHistoryInline(admin.TabularInline):
    model = RentalStatusHistory
    extra = 0
    readonly_fields = ['status', 'notes', 'changed_by', 'created_at']
    can_delete = False


@admin.register(BookRental)
class BookRentalAdmin(admin.ModelAdmin):
    list_display = [
        'rental_number', 'user_link', 'user_active_rentals', 'book_link', 'status_badge',
        'rental_price', 'due_date', 'days_info', 'renewal_count', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at', 'start_date', 'due_date', 'can_renew'
    ]
    search_fields = [
        'rental_number', 'user__email', 'user__full_name', 
        'book__title', 'book__author', 'transaction_id'
    ]
    readonly_fields = [
        'rental_number', 'rental_date', 'created_at', 'updated_at',
        'is_overdue', 'days_remaining', 'overdue_days', 'user_rental_summary'
    ]
    
    fieldsets = (
        ('Rental Information', {
            'fields': (
                'rental_number', 'user', 'user_rental_summary', 'book', 'rental_plan',
                'status', 'payment_status'
            )
        }),
        ('Pricing', {
            'fields': (
                'rental_price', 'security_deposit', 'total_amount',
                'late_fee', 'late_days'
            )
        }),
        ('Dates', {
            'fields': (
                'rental_date', 'start_date', 'due_date', 'return_date',
                'is_overdue', 'days_remaining', 'overdue_days'
            )
        }),
        ('Payment', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Renewal', {
            'fields': ('renewal_count', 'can_renew')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RentalStatusHistoryInline]
    
    actions = [
        'mark_as_active', 'mark_as_returned', 'mark_as_cancelled', 
        'calculate_late_fees', 'send_due_reminder', 'send_overdue_notice'
    ]
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    
    def user_active_rentals(self, obj):
        """Show user's active rentals count with color coding"""
        settings = RentalSettings.get_settings()
        active_count = BookRental.objects.filter(
            user=obj.user,
            status='active'
        ).count()
        
        max_rentals = settings.max_active_rentals_per_user
        
        if active_count >= max_rentals:
            color = '#DC3545'  # Red - at limit
            icon = '⚠️'
        elif active_count >= max_rentals - 1:
            color = '#FFA500'  # Orange - near limit
            icon = '⚡'
        else:
            color = '#28A745'  # Green - safe
            icon = '✓'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}/{}</span>',
            color, icon, active_count, max_rentals
        )
    user_active_rentals.short_description = 'Active Rentals'
    
    def user_rental_summary(self, obj):
        """Display user's complete rental summary"""
        settings = RentalSettings.get_settings()
        active_count = BookRental.objects.filter(user=obj.user, status='active').count()
        pending_count = BookRental.objects.filter(user=obj.user, status='pending').count()
        overdue_count = BookRental.objects.filter(user=obj.user, status='active', due_date__lt=timezone.now()).count()
        total_rentals = BookRental.objects.filter(user=obj.user).count()
        
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                <strong>User: {}</strong><br>
                <span style="color: #28A745;">Active: {}</span> | 
                <span style="color: #FFA500;">Pending: {}</span> | 
                <span style="color: #DC3545;">Overdue: {}</span><br>
                <span>Total Rentals: {}</span> | 
                <span>Max Allowed: {}</span>
                {}
            </div>
            ''',
            obj.user.full_name or obj.user.email,
            active_count,
            pending_count,
            overdue_count,
            total_rentals,
            settings.max_active_rentals_per_user,
            '<br><span style="color: red; font-weight: bold;">⚠️ AT MAXIMUM LIMIT</span>' 
            if active_count >= settings.max_active_rentals_per_user else ''
        )
    user_rental_summary.short_description = 'User Rental Summary'
    
    def book_link(self, obj):
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.title[:50])
    book_link.short_description = 'Book'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'active': '#28A745',
            'returned': '#6C757D',
            'overdue': '#DC3545',
            'cancelled': '#6C757D',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def days_info(self, obj):
        if obj.status == 'active':
            if obj.is_overdue:
                return format_html(
                    '<span style="color: red; font-weight: bold;">Overdue by {} days</span>',
                    obj.overdue_days
                )
            else:
                return format_html(
                    '<span style="color: green;">{} days remaining</span>',
                    obj.days_remaining
                )
        return '-'
    days_info.short_description = 'Days Info'
    
    def mark_as_active(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='active',
            start_date=timezone.now()
        )
        self.message_user(request, f'{updated} rental(s) marked as active.')
    mark_as_active.short_description = 'Mark selected rentals as Active'
    
    def mark_as_returned(self, request, queryset):
        count = 0
        for rental in queryset.filter(status='active'):
            rental.mark_as_returned()
            count += 1
        self.message_user(request, f'{count} rental(s) marked as returned.')
    mark_as_returned.short_description = 'Mark selected rentals as Returned'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'active']).update(status='cancelled')
        self.message_user(request, f'{updated} rental(s) cancelled.')
    mark_as_cancelled.short_description = 'Cancel selected rentals'
    
    def calculate_late_fees(self, request, queryset):
        count = 0
        total_fee = 0
        settings = RentalSettings.get_settings()
        for rental in queryset.filter(status='active'):
            if rental.is_overdue:
                fee = rental.calculate_late_fee(settings.daily_late_fee)
                total_fee += fee
                count += 1
        self.message_user(request, f'Calculated late fees for {count} rental(s). Total: ৳{total_fee}')
    calculate_late_fees.short_description = 'Calculate late fees for overdue rentals'
    
    def send_due_reminder(self, request, queryset):
        """Send due date reminder notifications"""
        count = 0
        for rental in queryset.filter(status='active'):
            if rental.days_remaining <= 3 and rental.days_remaining > 0:
                # Create notification
                RentalNotification.objects.create(
                    rental=rental,
                    user=rental.user,
                    notification_type='due_soon',
                    title=f'Reminder: Book Due in {rental.days_remaining} Days',
                    message=f'Your rental for "{rental.book.title}" is due on {rental.due_date.strftime("%d %b, %Y")}. Please return or renew it soon.'
                )
                count += 1
        self.message_user(request, f'Sent due date reminders for {count} rental(s).')
    send_due_reminder.short_description = 'Send due date reminder notifications'
    
    def send_overdue_notice(self, request, queryset):
        """Send overdue notices"""
        count = 0
        settings = RentalSettings.get_settings()
        for rental in queryset.filter(status='active'):
            if rental.is_overdue:
                late_fee = rental.calculate_late_fee(settings.daily_late_fee)
                RentalNotification.objects.create(
                    rental=rental,
                    user=rental.user,
                    notification_type='overdue',
                    title=f'⚠️ Book Overdue - Action Required',
                    message=f'Your rental for "{rental.book.title}" is {rental.overdue_days} day(s) overdue. Late fee: ৳{late_fee}. Please return the book immediately.'
                )
                count += 1
        self.message_user(request, f'Sent overdue notices for {count} rental(s).')
    send_overdue_notice.short_description = 'Send overdue notices'


@admin.register(RentalStatusHistory)
class RentalStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['rental', 'status', 'changed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['rental__rental_number', 'notes']
    readonly_fields = ['rental', 'status', 'notes', 'changed_by', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RentalFeedback)
class RentalFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'rental_link', 'user_link', 'book_link',
        'overall_rating', 'service_rating', 'book_condition_rating',
        'is_approved', 'created_at'
    ]
    list_filter = ['is_approved', 'overall_rating', 'created_at']
    search_fields = ['rental__rental_number', 'user__email', 'book__title', 'comment']
    readonly_fields = ['rental', 'user', 'book', 'created_at', 'updated_at', 'average_rating']
    list_editable = ['is_approved']
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('rental', 'user', 'book')
        }),
        ('Ratings', {
            'fields': (
                'overall_rating', 'service_rating', 'book_condition_rating', 'average_rating'
            )
        }),
        ('Comments', {
            'fields': ('comment', 'admin_response')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_feedback', 'unapprove_feedback']
    
    def rental_link(self, obj):
        url = reverse('admin:rentals_bookrental_change', args=[obj.rental.pk])
        return format_html('<a href="{}">{}</a>', url, obj.rental.rental_number)
    rental_link.short_description = 'Rental'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    
    def book_link(self, obj):
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.title[:50])
    book_link.short_description = 'Book'
    
    def approve_feedback(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} feedback(s) approved.')
    approve_feedback.short_description = 'Approve selected feedback'
    
    def unapprove_feedback(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} feedback(s) unapproved.')
    unapprove_feedback.short_description = 'Unapprove selected feedback'


@admin.register(RentalNotification)
class RentalNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'notification_type_badge', 'title',
        'read_status', 'is_sent', 'sent_at', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'is_sent', 'created_at'
    ]
    search_fields = ['user__email', 'user__full_name', 'title', 'message', 'rental__rental_number']
    readonly_fields = ['rental', 'user', 'notification_type', 'title', 'message', 'created_at', 'sent_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name or obj.user.email)
    user_link.short_description = 'User'
    
    def notification_type_badge(self, obj):
        """Display notification type with color coding"""
        colors = {
            'rental_confirmed': '#28A745',
            'rental_active': '#17A2B8',
            'due_soon': '#FFC107',
            'due_tomorrow': '#FD7E14',
            'overdue': '#DC3545',
            'returned': '#6C757D',
            'renewal_confirmed': '#20C997',
            'feedback_request': '#6F42C1',
        }
        color = colors.get(obj.notification_type, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'
    
    def read_status(self, obj):
        """Display read status with icon"""
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange; font-weight: bold;">● Unread</span>')
    read_status.short_description = 'Status'
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_sent', 'delete_read_notifications']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
    
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as sent.')
    mark_as_sent.short_description = 'Mark selected notifications as sent'
    
    def delete_read_notifications(self, request, queryset):
        count = queryset.filter(is_read=True).count()
        queryset.filter(is_read=True).delete()
        self.message_user(request, f'Deleted {count} read notification(s).')
    delete_read_notifications.short_description = 'Delete read notifications'


@admin.register(RentalSettings)
class RentalSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'security_deposit_percentage', 'daily_late_fee',
        'max_active_rentals_per_user', 'max_renewals', 'enable_notifications', 'rental_stats'
    ]
    
    fieldsets = (
        ('💰 Pricing Settings', {
            'fields': ('security_deposit_percentage', 'daily_late_fee'),
            'description': 'Configure rental pricing and fees. Security deposit is refundable on timely return.'
        }),
        ('📊 Rental Limits', {
            'fields': ('max_active_rentals_per_user', 'max_renewals', 'min_stock_for_rental'),
            'description': '''
                <strong>Important:</strong> 
                <ul>
                    <li><strong>Max Active Rentals:</strong> Maximum books one user can rent at the same time (Recommended: 3)</li>
                    <li><strong>Max Renewals:</strong> How many times a rental can be extended</li>
                    <li><strong>Min Stock:</strong> Minimum stock required to allow rental (prevents stock-out)</li>
                </ul>
            '''
        }),
        ('🔔 Notification Settings', {
            'fields': ('enable_notifications', 'due_soon_days'),
            'description': 'Control when and how users receive rental notifications'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def rental_stats(self, obj):
        """Display current rental statistics"""
        total_active = BookRental.objects.filter(status='active').count()
        total_overdue = BookRental.objects.filter(status='active', due_date__lt=timezone.now()).count()
        total_pending = BookRental.objects.filter(status='pending').count()
        
        users_at_limit = 0
        from django.db.models import Count
        user_rentals = BookRental.objects.filter(status='active').values('user').annotate(
            rental_count=Count('id')
        )
        for ur in user_rentals:
            if ur['rental_count'] >= obj.max_active_rentals_per_user:
                users_at_limit += 1
        
        return format_html(
            '''
            <div style="background: #e8f4f8; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8;">
                <strong>📊 Current Rental Statistics:</strong><br><br>
                <span style="color: #28A745;">✓ Active Rentals: <strong>{}</strong></span><br>
                <span style="color: #DC3545;">⚠️ Overdue: <strong>{}</strong></span><br>
                <span style="color: #FFA500;">⏳ Pending: <strong>{}</strong></span><br>
                <span style="color: #6C757D;">👥 Users at Max Limit: <strong>{}</strong></span>
            </div>
            ''',
            total_active, total_overdue, total_pending, users_at_limit
        )
    rental_stats.short_description = 'Statistics'
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not RentalSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)
