# Support System Quick Guide

## 🎯 Overview

The BookShop support system now has a clear separation between customer and staff interfaces.

## 👥 For Customers

### How to Get Support

1. **Look for the Chat Button**
   - Located at the bottom-right corner of every page
   - Blue/teal circular button with a chat icon
   - Available on all pages when logged in

2. **Click to Chat**
   - Click the chat button to open the widget
   - Widget opens as an overlay (you stay on your current page)
   - No need to navigate away

3. **Send Messages**
   - Type your message in the input box
   - Press Enter or click the send button
   - Attach files if needed (screenshots, documents)

4. **Get Help**
   - Support agent will respond in real-time
   - All messages are saved automatically
   - Continue conversations anytime

### What Customers See

✅ **Chat Widget** (Primary Interface)
- Floating button at bottom-right
- Click to open/close
- Real-time messaging
- File attachments
- Conversation history

❌ **NO Support Conversation Pages**
- Customers should NOT use full-page conversation views
- If you navigate to support pages, you'll see a guide to use the widget instead

### Navigation Menu Items (Customers)

- ✅ Profile
- ✅ My Orders
- ✅ My Rentals
- ✅ Addresses
- ❌ ~~Support Conversations~~ (Removed - use chat widget instead)

---

## 👔 For Staff/Agents

### Access Points

1. **Agent Dashboard**
   - Menu → Agent Dashboard
   - URL: `/support/agent/dashboard/`
   - Manage all conversations
   - View active chats
   - Quick replies

2. **Support Messages**
   - Menu → Support Messages
   - URL: `/support/conversations/`
   - View all conversation history
   - Access individual conversations

3. **Conversation Details**
   - Click any conversation to open full view
   - Send messages
   - View customer details
   - Update conversation status

### Navigation Menu Items (Staff)

- ✅ Profile
- ✅ My Orders
- ✅ My Rentals
- ✅ Addresses
- ✅ **Support Messages** (Staff only)
- ✅ **Agent Dashboard** (Staff only)
- ✅ Admin Panel

---

## 🔧 Technical Details

### Chat Widget Features

1. **Auto-initialization**
   - Loads automatically on every page
   - Checks if chat is enabled
   - Fetches configuration from server

2. **Real-time Messaging**
   - Polls for new messages every 3 seconds
   - Shows typing indicators
   - Read receipts

3. **File Upload**
   - Images: jpg, jpeg, png, gif
   - Documents: pdf, doc, docx, txt
   - Max file size: 5MB (configurable)

4. **Conversation Management**
   - Creates conversation on first message
   - Auto-assigns to available agent
   - Maintains conversation history

### API Endpoints

**Customer APIs:**
- `GET /support/api/config/` - Get widget configuration
- `GET /support/api/conversation/create/` - Create/get conversation
- `GET /support/api/conversation/<id>/messages/` - Get messages
- `POST /support/api/conversation/<id>/send/` - Send message
- `POST /support/api/conversation/<id>/upload/` - Upload file
- `POST /support/api/conversation/<id>/close/` - Close conversation

**Agent APIs:**
- `GET /support/agent/api/conversations/` - Get all conversations
- `GET /support/agent/api/conversation/<id>/messages/` - Get messages
- `POST /support/agent/api/send/` - Send message as agent
- `POST /support/agent/api/conversation/<id>/update/` - Update conversation
- `POST /support/agent/api/toggle-online/` - Toggle agent online status

### Views

**Customer Views:**
- `my_conversations` - Landing page with chat widget guide
- `conversation_detail` - Restricted (redirects customers to widget)

**Agent Views:**
- `agent_dashboard` - Main agent interface
- `agent_conversation_detail` - Full conversation management

---

## 🎨 User Interface

### Chat Widget (Customer)

```
┌─────────────────────────────────┐
│ [👤] Customer Support      [−][×]│
│ ⚫ Support is online            │
├─────────────────────────────────┤
│                                 │
│  [Agent] Hello! How can I help? │
│         You: I need help!  [Me] │
│  [Agent] Sure, what's the issue?│
│                                 │
├─────────────────────────────────┤
│ [😊][📎] Type message... [Send] │
└─────────────────────────────────┘
```

### Support Messages Page (Customer)

```
┌─────────────────────────────────────┐
│  🎯 Need Help? Use Our Chat Widget! │
│                                     │
│  For the best support experience,   │
│  use our live chat widget          │
│                                     │
│     [📱 Open Chat Widget]           │
│                                     │
│  Why Use the Chat Widget?          │
│  ⚡ Instant Response               │
│  🕐 Conversation History           │
│  📎 File Attachments               │
│  🛡️ Dedicated Support Agent        │
│                                     │
│  Look for the chat button ↓        │
│     [💬 Chat with Support]         │
└─────────────────────────────────────┘
```

---

## 📋 Common Tasks

### For Customers

**Start a conversation:**
1. Click chat button (bottom-right)
2. Type your message
3. Press Enter

**Upload a file:**
1. Open chat widget
2. Click paperclip icon
3. Select file
4. File uploads automatically

**Check conversation history:**
1. Open chat widget
2. Scroll up to see previous messages
3. All messages are saved

### For Staff

**Respond to customer:**
1. Go to Agent Dashboard
2. Click on active conversation
3. Type response and send

**Assign conversation:**
1. Open conversation
2. Select agent from dropdown
3. Save changes

**Close conversation:**
1. Open conversation
2. Change status to "Closed"
3. Conversation archived

---

## 🚀 Best Practices

### For Customers

1. ✅ Use the chat widget for all support needs
2. ✅ Be clear and specific in your messages
3. ✅ Attach screenshots if reporting issues
4. ✅ Keep the chat widget open while waiting for response
5. ❌ Don't use multiple channels (stick to chat)

### For Staff

1. ✅ Respond promptly to customer messages
2. ✅ Use quick replies for common questions
3. ✅ Mark yourself as online when available
4. ✅ Update conversation status appropriately
5. ✅ Close conversations when resolved

---

## 🔍 Troubleshooting

### Chat Widget Not Showing

**Check:**
1. Is the user logged in?
2. Is chat enabled in settings?
3. Are chat CSS/JS files loaded?
4. Check browser console for errors

**Fix:**
```bash
# Verify chat settings
python manage.py shell
>>> from support.models import ChatSettings
>>> ChatSettings.get_settings().is_enabled
True
```

### Messages Not Sending

**Check:**
1. Internet connection
2. User authentication
3. CSRF token
4. Server logs

### Agent Not Receiving Messages

**Check:**
1. Agent is online
2. Conversation is assigned
3. Polling is working
4. WebSocket connection (if enabled)

---

## 📞 Support

For technical issues with the support system itself, contact the development team.

**System Status:**
- Chat Widget: ✅ Active
- Agent Dashboard: ✅ Active
- File Upload: ✅ Active
- Real-time Messaging: ✅ Active

**Last Updated:** 2025-11-10
