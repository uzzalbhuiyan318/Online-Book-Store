from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from .models import SupportAgent, Conversation, Message, QuickReply, ChatSettings


@admin.register(SupportAgent)
class SupportAgentAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'display_name_bn', 'email', 'online_status', 'is_active', 'last_seen', 'order']
    list_filter = ['is_online', 'is_active', 'created_at']
    search_fields = ['display_name', 'display_name_bn', 'email', 'user__email', 'user__full_name']
    list_editable = ['is_active', 'order']
    readonly_fields = ['last_seen', 'created_at', 'avatar_preview']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'display_name', 'display_name_bn', 'email', 'avatar', 'avatar_preview')
        }),
        (_('Status'), {
            'fields': ('is_online', 'is_active', 'last_seen')
        }),
        (_('Bio'), {
            'fields': ('bio', 'bio_bn')
        }),
        (_('Display Settings'), {
            'fields': ('order',)
        }),
    )
    
    def online_status(self, obj):
        if obj.is_online:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Online</span>'
            )
        return format_html(
            '<span style="color: gray;">○ Offline</span>'
        )
    online_status.short_description = _('Status')
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 50%;" />', obj.avatar.url)
        return _('No avatar')
    avatar_preview.short_description = _('Avatar Preview')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'is_agent', 'message_type', 'content', 'is_read', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'user_link', 'assigned_agent', 'status_badge', 'priority_badge', 'language', 'unread_counts', 'last_message_at']
    list_filter = ['status', 'priority', 'language', 'is_archived', 'created_at', 'assigned_agent']
    search_fields = ['conversation_id', 'user__full_name', 'user__email', 'subject']
    readonly_fields = ['conversation_id', 'user_unread_count', 'agent_unread_count', 'last_message_at', 'created_at', 'updated_at']
    date_hierarchy = None
    inlines = [MessageInline]
    
    fieldsets = (
        (_('Conversation Info'), {
            'fields': ('conversation_id', 'user', 'subject', 'language')
        }),
        (_('Assignment'), {
            'fields': ('assigned_agent', 'status', 'priority')
        }),
        (_('Statistics'), {
            'fields': ('user_unread_count', 'agent_unread_count', 'last_message_at')
        }),
        (_('Archive'), {
            'fields': ('is_archived',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_closed', 'assign_to_me', 'mark_as_high_priority']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = _('User')
    
    def status_badge(self, obj):
        colors = {
            'open': 'success',
            'pending': 'warning',
            'resolved': 'info',
            'closed': 'secondary'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def priority_badge(self, obj):
        colors = {
            'low': 'secondary',
            'normal': 'primary',
            'high': 'warning',
            'urgent': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.priority, 'primary'),
            obj.get_priority_display()
        )
    priority_badge.short_description = _('Priority')
    
    def unread_counts(self, obj):
        return format_html(
            'User: <b>{}</b> | Agent: <b>{}</b>',
            obj.user_unread_count,
            obj.agent_unread_count
        )
    unread_counts.short_description = _('Unread Messages')
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} conversations marked as resolved.')
    mark_as_resolved.short_description = _('Mark selected as resolved')
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} conversations marked as closed.')
    mark_as_closed.short_description = _('Mark selected as closed')
    
    def assign_to_me(self, request, queryset):
        try:
            agent = SupportAgent.objects.get(user=request.user)
            updated = queryset.update(assigned_agent=agent)
            self.message_user(request, f'{updated} conversations assigned to you.')
        except SupportAgent.DoesNotExist:
            self.message_user(request, 'You are not registered as a support agent.', level='error')
    assign_to_me.short_description = _('Assign selected to me')
    
    def mark_as_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} conversations marked as high priority.')
    mark_as_high_priority.short_description = _('Mark as high priority')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_link', 'sender', 'message_preview', 'message_type', 'is_agent', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_agent', 'is_read', 'created_at']
    search_fields = ['content', 'conversation__conversation_id', 'sender__full_name', 'sender__email']
    readonly_fields = ['conversation', 'sender', 'is_agent', 'created_at', 'read_at', 'edited_at', 'attachment_preview']
    date_hierarchy = None
    
    fieldsets = (
        (_('Message Info'), {
            'fields': ('conversation', 'sender', 'is_agent', 'message_type')
        }),
        (_('Content'), {
            'fields': ('content',)
        }),
        (_('Attachment'), {
            'fields': ('attachment', 'attachment_name', 'attachment_preview')
        }),
        (_('Status'), {
            'fields': ('is_read', 'read_at', 'is_edited', 'edited_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',)
        }),
    )
    
    def conversation_link(self, obj):
        url = reverse('admin:support_conversation_change', args=[obj.conversation.id])
        return format_html('<a href="{}">{}</a>', url, obj.conversation.conversation_id)
    conversation_link.short_description = _('Conversation')
    
    def message_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    message_preview.short_description = _('Message')
    
    def attachment_preview(self, obj):
        if obj.attachment:
            if obj.message_type == 'image':
                return format_html('<img src="{}" width="200" />', obj.attachment.url)
            return format_html('<a href="{}" target="_blank">{}</a>', obj.attachment.url, obj.attachment_name or 'Download')
        return _('No attachment')
    attachment_preview.short_description = _('Attachment Preview')


@admin.register(QuickReply)
class QuickReplyAdmin(admin.ModelAdmin):
    list_display = ['title', 'title_bn', 'category', 'is_active', 'order']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'title_bn', 'content', 'content_bn']
    list_editable = ['is_active', 'order']
    
    fieldsets = (
        (_('English Version'), {
            'fields': ('title', 'content')
        }),
        (_('Bengali Version'), {
            'fields': ('title_bn', 'content_bn')
        }),
        (_('Settings'), {
            'fields': ('category', 'is_active', 'order')
        }),
    )


@admin.register(ChatSettings)
class ChatSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('General Settings'), {
            'fields': ('is_enabled', 'widget_position', 'primary_color', 'show_online_status')
        }),
        (_('Welcome Messages'), {
            'fields': ('welcome_message', 'welcome_message_bn')
        }),
        (_('Offline Messages'), {
            'fields': ('offline_message', 'offline_message_bn')
        }),
        (_('Assignment & Limits'), {
            'fields': ('auto_assign', 'max_file_size')
        }),
        (_('Business Hours'), {
            'fields': ('business_hours_start', 'business_hours_end')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not ChatSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
