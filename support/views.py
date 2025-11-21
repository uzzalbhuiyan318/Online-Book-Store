from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, F
from django.core.files.storage import default_storage
from .models import Conversation, Message, SupportAgent, ChatSettings, QuickReply
import json


def get_chat_settings():
    """Get or create chat settings"""
    return ChatSettings.get_settings()


@require_http_methods(["GET"])
def chat_widget_config(request):
    """API endpoint to get chat widget configuration"""
    settings = get_chat_settings()
    online_agents = SupportAgent.objects.filter(is_online=True, is_active=True)
    
    # Determine language
    lang = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'en'
    
    # Get welcome message based on language
    if lang == 'bn':
        welcome_msg = settings.welcome_message_bn
        offline_msg = settings.offline_message_bn
    else:
        welcome_msg = settings.welcome_message
        offline_msg = settings.offline_message
    
    config = {
        'enabled': settings.is_enabled,
        'position': settings.widget_position,
        'primary_color': settings.primary_color,
        'show_online_status': settings.show_online_status,
        'welcome_message': welcome_msg,
        'offline_message': offline_msg,
        'agents_online': online_agents.count(),
        'max_file_size': settings.max_file_size * 1024 * 1024,  # Convert MB to bytes
    }
    
    return JsonResponse(config)


@login_required
@require_http_methods(["GET"])
def get_or_create_conversation(request):
    """Get active conversation or create new one"""
    # Get or create active conversation for user
    conversation = Conversation.objects.filter(
        user=request.user,
        status__in=['open', 'pending']
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(
            user=request.user,
            language=request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'en',
            status='pending'  # Set as pending until an agent replies
        )
        
        # Do NOT auto-assign - let first agent to reply get assigned
        # Send welcome message as system message
        settings = get_chat_settings()
        Message.objects.create(
            conversation=conversation,
            sender=request.user,  # System message from customer's perspective
            is_agent=False,
            message_type='system',
            content=settings.welcome_message if request.LANGUAGE_CODE == 'en' else settings.welcome_message_bn
        )
    
    return JsonResponse({
        'conversation_id': conversation.conversation_id,
        'status': conversation.status,
        'agent': {
            'name': conversation.assigned_agent.display_name if conversation.assigned_agent else None,
            'name_bn': conversation.assigned_agent.display_name_bn if conversation.assigned_agent else None,
            'avatar': conversation.assigned_agent.get_avatar_url() if conversation.assigned_agent else None,
            'is_online': conversation.assigned_agent.is_online if conversation.assigned_agent else False,
        } if conversation.assigned_agent else None
    })


@login_required
@require_http_methods(["GET"])
def get_messages(request, conversation_id):
    """Get messages for a conversation"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    # Check if user has access (either customer or agent)
    is_agent = hasattr(request.user, 'support_agent') and request.user.is_staff
    if not is_agent and conversation.user != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get after parameter for polling
    after_id = request.GET.get('after', 0)
    
    # Get messages
    if after_id:
        messages = Message.objects.filter(
            conversation=conversation,
            id__gt=after_id
        ).select_related('sender').order_by('created_at')
    else:
        messages = Message.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('created_at')
    
    # Mark unread messages as read
    if not is_agent:
        unread_messages = messages.filter(is_read=False, is_agent=True)
        unread_messages.update(is_read=True, read_at=timezone.now())
        conversation.user_unread_count = 0
        conversation.save(update_fields=['user_unread_count'])
    else:
        unread_messages = messages.filter(is_read=False, is_agent=False)
        unread_messages.update(is_read=True, read_at=timezone.now())
        conversation.agent_unread_count = 0
        conversation.save(update_fields=['agent_unread_count'])
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_name': msg.sender.full_name,
            'sender_avatar': msg.sender.profile_image.url if hasattr(msg.sender, 'profile_image') and msg.sender.profile_image else None,
            'is_agent': msg.is_agent,
            'message_type': msg.message_type,
            'content': msg.content,
            'attachment': msg.attachment.url if msg.attachment else None,
            'attachment_name': msg.attachment_name,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat(),
        })
    
    return JsonResponse({'messages': messages_data})


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            is_agent=False,
            message_type='text',
            content=content
        )
        
        # Update conversation - mark as open if it was pending
        conversation.last_message_at = timezone.now()
        conversation.agent_unread_count = F('agent_unread_count') + 1
        if conversation.status == 'pending':
            conversation.status = 'open'
        conversation.save(update_fields=['last_message_at', 'agent_unread_count', 'status'])
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_attachment(request, conversation_id):
    """Upload file attachment"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id, user=request.user)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    settings = get_chat_settings()
    max_size = settings.max_file_size * 1024 * 1024  # Convert MB to bytes
    
    if file.size > max_size:
        return JsonResponse({'error': f'File size exceeds {settings.max_file_size}MB limit'}, status=400)
    
    # Determine message type
    message_type = 'file'
    if file.content_type.startswith('image/'):
        message_type = 'image'
    
    # Create message with attachment
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        is_agent=False,
        message_type=message_type,
        content=request.POST.get('content', 'Sent an attachment'),
        attachment=file,
        attachment_name=file.name
    )
    
    # Update conversation
    conversation.last_message_at = timezone.now()
    conversation.agent_unread_count = F('agent_unread_count') + 1
    conversation.save(update_fields=['last_message_at', 'agent_unread_count'])
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'attachment': message.attachment.url,
            'attachment_name': message.attachment_name,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
        }
    })


@login_required
@require_http_methods(["POST"])
def close_conversation(request, conversation_id):
    """Close a conversation"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id, user=request.user)
    
    conversation.status = 'closed'
    conversation.save(update_fields=['status'])
    
    return JsonResponse({'success': True})


@login_required
def my_conversations(request):
    """View all user conversations"""
    conversations = Conversation.objects.filter(user=request.user).prefetch_related('messages')
    
    return render(request, 'support/my_conversations.html', {
        'conversations': conversations
    })


@login_required
def conversation_detail(request, conversation_id):
    """View conversation details - Staff only, customers should use chat widget"""
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id, user=request.user)
    
    # Redirect non-staff users to use the chat widget
    if not request.user.is_staff:
        from django.contrib import messages as django_messages
        django_messages.info(request, 'Please use the chat widget at the bottom-right corner for support.')
        return redirect('support:my_conversations')
    
    messages = Message.objects.filter(conversation=conversation).select_related('sender')
    
    # Mark messages as read
    unread_messages = messages.filter(is_read=False, is_agent=True)
    unread_messages.update(is_read=True, read_at=timezone.now())
    conversation.user_unread_count = 0
    conversation.save(update_fields=['user_unread_count'])
    
    return render(request, 'support/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages
    })
