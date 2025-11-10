from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator


class SupportAgent(models.Model):
    """Model for support agents"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_agent')
    display_name = models.CharField(max_length=100, verbose_name=_("Display Name"))
    display_name_bn = models.CharField(max_length=100, blank=True, verbose_name=_("Display Name (Bengali)"))
    avatar = models.ImageField(upload_to='support/agents/', blank=True, null=True, verbose_name=_("Avatar"))
    is_online = models.BooleanField(default=False, verbose_name=_("Is Online"))
    bio = models.TextField(blank=True, verbose_name=_("Bio"))
    bio_bn = models.TextField(blank=True, verbose_name=_("Bio (Bengali)"))
    email = models.EmailField(verbose_name=_("Email"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    last_seen = models.DateTimeField(auto_now=True, verbose_name=_("Last Seen"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-is_online', 'display_name']
        verbose_name = _("Support Agent")
        verbose_name_plural = _("Support Agents")
    
    def __str__(self):
        return self.display_name
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


class Conversation(models.Model):
    """Model for chat conversations"""
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('pending', _('Pending')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('normal', _('Normal')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    conversation_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_conversations')
    assigned_agent = models.ForeignKey(SupportAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conversations')
    subject = models.CharField(max_length=255, blank=True, verbose_name=_("Subject"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name=_("Status"))
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name=_("Priority"))
    language = models.CharField(max_length=10, default='en', verbose_name=_("Language"))
    is_archived = models.BooleanField(default=False, verbose_name=_("Archived"))
    user_unread_count = models.IntegerField(default=0, verbose_name=_("User Unread Count"))
    agent_unread_count = models.IntegerField(default=0, verbose_name=_("Agent Unread Count"))
    last_message_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Last Message At"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
    
    def __str__(self):
        return f"{self.conversation_id} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.conversation_id:
            import uuid
            self.conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class Message(models.Model):
    """Model for chat messages"""
    MESSAGE_TYPE_CHOICES = [
        ('text', _('Text')),
        ('image', _('Image')),
        ('file', _('File')),
        ('system', _('System')),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    is_agent = models.BooleanField(default=False, verbose_name=_("Is Agent Message"))
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text', verbose_name=_("Message Type"))
    content = models.TextField(verbose_name=_("Content"))
    
    # File attachments
    attachment = models.FileField(
        upload_to='support/attachments/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt'])],
        verbose_name=_("Attachment")
    )
    attachment_name = models.CharField(max_length=255, blank=True, verbose_name=_("Attachment Name"))
    
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Read At"))
    is_edited = models.BooleanField(default=False, verbose_name=_("Is Edited"))
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Edited At"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
    
    def __str__(self):
        return f"{self.sender.full_name}: {self.content[:50]}"


class QuickReply(models.Model):
    """Model for predefined quick replies"""
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    title_bn = models.CharField(max_length=100, blank=True, verbose_name=_("Title (Bengali)"))
    content = models.TextField(verbose_name=_("Content"))
    content_bn = models.TextField(blank=True, verbose_name=_("Content (Bengali)"))
    category = models.CharField(max_length=50, blank=True, verbose_name=_("Category"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = _("Quick Reply")
        verbose_name_plural = _("Quick Replies")
    
    def __str__(self):
        return self.title


class ChatSettings(models.Model):
    """Model for chat widget settings"""
    is_enabled = models.BooleanField(default=True, verbose_name=_("Enable Chat Widget"))
    welcome_message = models.TextField(default="Hello! How can we help you today?", verbose_name=_("Welcome Message"))
    welcome_message_bn = models.TextField(default="আসসালামু আলাইকুম, রকমারি উটকসে স আপনাকে স্বাগতম। অনুগ্রহ করে জানাবেন কিভাবে সহযোগিতা করতে পারি।", verbose_name=_("Welcome Message (Bengali)"))
    offline_message = models.TextField(default="We're currently offline. Please leave a message.", verbose_name=_("Offline Message"))
    offline_message_bn = models.TextField(default="আমরা এই মুহূর্তে অফলাইনে আছি। অনুগ্রহ করে একটি বার্তা রেখে যান।", verbose_name=_("Offline Message (Bengali)"))
    widget_position = models.CharField(max_length=20, default='bottom-right', choices=[
        ('bottom-right', _('Bottom Right')),
        ('bottom-left', _('Bottom Left')),
    ], verbose_name=_("Widget Position"))
    primary_color = models.CharField(max_length=7, default='#008B8B', verbose_name=_("Primary Color"))
    auto_assign = models.BooleanField(default=True, verbose_name=_("Auto Assign to Agent"))
    max_file_size = models.IntegerField(default=5, verbose_name=_("Max File Size (MB)"))
    business_hours_start = models.TimeField(default='09:00', verbose_name=_("Business Hours Start"))
    business_hours_end = models.TimeField(default='18:00', verbose_name=_("Business Hours End"))
    show_online_status = models.BooleanField(default=True, verbose_name=_("Show Online Status"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Chat Settings")
        verbose_name_plural = _("Chat Settings")
    
    def __str__(self):
        return "Chat Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
