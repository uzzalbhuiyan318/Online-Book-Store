from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, F, Count
from .models import Conversation, Message, SupportAgent, ChatSettings, QuickReply
import json


def is_support_agent(user):
    """Check if user is a support agent"""
    return hasattr(user, 'support_agent') and user.is_staff


@login_required
@user_passes_test(is_support_agent)
def agent_dashboard(request):
    """Agent dashboard to handle customer conversations"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return render(request, 'support/agent_not_found.html')
    
    # Get all open conversations
    conversations = Conversation.objects.filter(
        status__in=['open', 'pending']
    ).select_related('user', 'assigned_agent').annotate(
        message_count=Count('messages')
    ).order_by('-agent_unread_count', '-last_message_at')
    
    # Get quick replies for this agent
    quick_replies = QuickReply.objects.filter(is_active=True)
    
    # Get chat settings
    settings = ChatSettings.get_settings()
    
    context = {
        'agent': agent,
        'conversations': conversations,
        'quick_replies': quick_replies,
        'settings': settings,
    }
    
    return render(request, 'support/agent_dashboard.html', context)


@login_required
@user_passes_test(is_support_agent)
def agent_conversation_detail(request, conversation_id):
    """Agent view for a specific conversation with real-time messaging"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    # Mark messages as read by agent
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False,
        is_agent=False
    )
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Reset agent unread count
    conversation.agent_unread_count = 0
    conversation.save(update_fields=['agent_unread_count'])
    
    # Get messages
    messages = Message.objects.filter(conversation=conversation).select_related('sender').order_by('created_at')
    
    # Get quick replies
    quick_replies = QuickReply.objects.filter(is_active=True)
    
    context = {
        'agent': agent,
        'conversation': conversation,
        'messages': messages,
        'quick_replies': quick_replies,
    }
    
    return render(request, 'support/agent_conversation.html', context)


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["GET"])
def agent_get_conversations(request):
    """API endpoint to get all conversations for agent dashboard"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'open,pending')
    statuses = status_filter.split(',')
    
    conversations = Conversation.objects.filter(
        status__in=statuses
    ).select_related('user', 'assigned_agent').order_by('-last_message_at')
    
    conversations_data = []
    for conv in conversations:
        last_message = conv.messages.last()
        conversations_data.append({
            'id': conv.id,
            'conversation_id': conv.conversation_id,
            'user': {
                'name': conv.user.full_name,
                'email': conv.user.email,
                'avatar': conv.user.profile_image.url if conv.user.profile_image else None,
            },
            'assigned_agent': {
                'name': conv.assigned_agent.display_name if conv.assigned_agent else None,
            } if conv.assigned_agent else None,
            'status': conv.status,
            'priority': conv.priority,
            'agent_unread_count': conv.agent_unread_count,
            'last_message': {
                'content': last_message.content[:50] if last_message else '',
                'created_at': last_message.created_at.isoformat() if last_message else None,
            } if last_message else None,
            'last_message_at': conv.last_message_at.isoformat(),
        })
    
    return JsonResponse({'conversations': conversations_data})


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["GET"])
def agent_get_messages(request, conversation_id):
    """API endpoint to get messages for a conversation (agent view)"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    # Get last message ID from request to only return new messages
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages = Message.objects.filter(
        conversation=conversation,
        id__gt=last_message_id
    ).select_related('sender').order_by('created_at')
    
    # Mark new messages as read by agent
    unread_messages = messages.filter(is_read=False, is_agent=False)
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Update conversation
    if unread_messages.exists():
        conversation.agent_unread_count = 0
        conversation.save(update_fields=['agent_unread_count'])
    
    messages_data = []
    for msg in messages:
        # Get sender avatar
        sender_avatar = None
        if hasattr(msg.sender, 'profile_image') and msg.sender.profile_image:
            sender_avatar = msg.sender.profile_image.url
        
        messages_data.append({
            'id': msg.id,
            'sender_name': msg.sender.full_name,
            'sender_avatar': sender_avatar,
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
@user_passes_test(is_support_agent)
@require_http_methods(["POST"])
def agent_send_message(request):
    """API endpoint for agent to send a message"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not a support agent'}, status=403)
    
    conversation_id = request.POST.get('conversation_id')
    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')
    attachment = request.FILES.get('attachment')
    
    if not conversation_id:
        return JsonResponse({'success': False, 'message': 'Conversation ID is required'}, status=400)
    
    if not content and not attachment:
        return JsonResponse({'success': False, 'message': 'Message content or attachment is required'}, status=400)
    
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    try:
        # Assign conversation to agent if not assigned
        if not conversation.assigned_agent:
            conversation.assigned_agent = agent
            conversation.save(update_fields=['assigned_agent'])
        
        # Create message
        message_data = {
            'conversation': conversation,
            'sender': request.user,
            'is_agent': True,
            'message_type': message_type,
            'content': content or 'Sent an attachment',
            'is_read': False  # Customer hasn't read it yet
        }
        
        # Add attachment if present
        if attachment:
            message_data['attachment'] = attachment
            message_data['attachment_name'] = attachment.name
        
        message = Message.objects.create(**message_data)
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.user_unread_count = F('user_unread_count') + 1
        conversation.save(update_fields=['last_message_at', 'user_unread_count'])
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_name': request.user.full_name,
                'sender_avatar': request.user.profile_image.url if hasattr(request.user, 'profile_image') and request.user.profile_image else None,
                'is_agent': True,
                'message_type': message.message_type,
                'attachment': message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment_name
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["POST"])
def agent_update_conversation(request, conversation_id):
    """API endpoint to update conversation status, priority, etc."""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    try:
        data = json.loads(request.body)
        
        # Update status
        if 'status' in data:
            conversation.status = data['status']
        
        # Update priority
        if 'priority' in data:
            conversation.priority = data['priority']
        
        # Assign to agent
        if 'assign_to_me' in data and data['assign_to_me']:
            conversation.assigned_agent = agent
        
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'status': conversation.status,
                'priority': conversation.priority,
                'assigned_agent': agent.display_name if conversation.assigned_agent else None,
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["POST"])
def agent_toggle_online(request):
    """Toggle agent online/offline status"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
        agent.is_online = not agent.is_online
        agent.save(update_fields=['is_online'])
        
        return JsonResponse({
            'success': True,
            'is_online': agent.is_online
        })
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["GET"])
def agent_get_quick_replies(request):
    """Get all active quick replies"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    category = request.GET.get('category', '')
    
    quick_replies = QuickReply.objects.filter(is_active=True)
    
    if category:
        quick_replies = quick_replies.filter(category=category)
    
    replies_data = []
    for reply in quick_replies:
        replies_data.append({
            'id': reply.id,
            'title': reply.title,
            'title_bn': reply.title_bn,
            'content': reply.content,
            'content_bn': reply.content_bn,
            'category': reply.category,
        })
    
    return JsonResponse({'quick_replies': replies_data})


@login_required
@user_passes_test(is_support_agent)
@require_http_methods(["POST"])
def agent_mark_messages_read(request, conversation_id):
    """Mark all messages in a conversation as read by agent"""
    try:
        agent = SupportAgent.objects.get(user=request.user)
    except SupportAgent.DoesNotExist:
        return JsonResponse({'error': 'Not a support agent'}, status=403)
    
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    # Mark all unread customer messages as read
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False,
        is_agent=False
    )
    unread_count = unread_messages.count()
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Reset agent unread count
    conversation.agent_unread_count = 0
    conversation.save(update_fields=['agent_unread_count'])
    
    return JsonResponse({
        'success': True,
        'marked_read': unread_count
    })
