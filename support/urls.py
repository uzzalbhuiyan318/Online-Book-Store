from django.urls import path
from . import views, agent_views

app_name = 'support'

urlpatterns = [
    # Customer API endpoints
    path('api/config/', views.chat_widget_config, name='chat_config'),
    path('api/conversation/create/', views.get_or_create_conversation, name='create_conversation'),
    path('api/conversation/<str:conversation_id>/messages/', views.get_messages, name='get_messages'),
    path('api/conversation/<str:conversation_id>/send/', views.send_message, name='send_message'),
    path('api/conversation/<str:conversation_id>/upload/', views.upload_attachment, name='upload_attachment'),
    path('api/conversation/<str:conversation_id>/close/', views.close_conversation, name='close_conversation'),
    
    # Customer frontend pages
    path('conversations/', views.my_conversations, name='my_conversations'),
    path('conversation/<str:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Agent Dashboard
    path('agent/dashboard/', agent_views.agent_dashboard, name='agent_dashboard'),
    path('agent/conversation/<str:conversation_id>/', agent_views.agent_conversation_detail, name='agent_conversation'),
    
    # Agent API endpoints
    path('api/conversations/', agent_views.agent_get_conversations, name='agent_get_conversations'),
    path('api/conversation/<str:conversation_id>/messages/', agent_views.agent_get_messages, name='agent_get_messages'),
    path('api/conversation/<str:conversation_id>/mark-read/', agent_views.agent_mark_messages_read, name='agent_mark_read'),
    path('agent/api/send/', agent_views.agent_send_message, name='agent_send_message'),
    path('agent/api/conversation/<str:conversation_id>/update/', agent_views.agent_update_conversation, name='agent_update_conversation'),
    path('agent/api/toggle-online/', agent_views.agent_toggle_online, name='agent_toggle_online'),
    path('agent/api/quick-replies/', agent_views.agent_get_quick_replies, name='agent_quick_replies'),
]
