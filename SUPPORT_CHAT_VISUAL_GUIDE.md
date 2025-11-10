# 🎨 Customer Support Chat System - Visual Overview

## 🖼️ What You'll See

### 1. CHAT WIDGET (Customer View)

```
┌─────────────────────────────────────┐
│  🟢 Chat                        ✕   │ ← Header (Teal #008B8B)
│  👤 rokomari                        │ ← Agent Name
│  ● Support is online                │ ← Status
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────┐           │ ← Agent Message
│  │ আসসালামু আলাইকুম,  │           │   (White Bubble)
│  │ রকমারি উটকসে স     │           │
│  │ আপনাকে স্বাগতম।    │           │
│  └─────────────────────┘           │
│                                     │
│            ┌────────────────────┐  │ ← User Message
│            │ I need help with   │  │   (Teal Bubble)
│            │ my order          │  │
│            └────────────────────┘  │
│                                     │
├─────────────────────────────────────┤
│ [Compose message...]  😊 📎 ➤      │ ← Input Area
└─────────────────────────────────────┘
    ↓ Minimized:
  [💬 2]  ← Floating Button
```

### 2. ADMIN PANEL (Agent View)

```
CONVERSATIONS LIST
┌────────────────────────────────────────────────────────┐
│ ID          User        Status    Priority  Unread     │
├────────────────────────────────────────────────────────┤
│ CONV-ABC    John Doe    [Open]    [High]    3         │
│ CONV-XYZ    Jane Smith  [Pending] [Normal]  1         │
│ CONV-123    Ali Khan    [Resolved][Low]     0         │
└────────────────────────────────────────────────────────┘

CONVERSATION DETAIL
┌────────────────────────────────────────────────────────┐
│ CONV-ABC123 | Assigned: rokomari | Status: Open       │
├────────────────────────────────────────────────────────┤
│ Customer: I need help with my order                    │
│ Agent: Hello! I'd be happy to help. What's your        │
│        order number?                                    │
│ Customer: ORDER-12345                                   │
│ [Reply message inline...]                              │
└────────────────────────────────────────────────────────┘

CHAT SETTINGS
┌────────────────────────────────────────────────────────┐
│ ☑ Enable Chat Widget                                   │
│ Widget Position: [Bottom Right ▼]                      │
│ Primary Color: [#008B8B] (Color Picker)               │
│ Welcome Message: [Hello! How can we help...]          │
│ Welcome Message BN: [আসসালামু আলাইকুম...]             │
│ Max File Size: [5] MB                                  │
│ ☑ Auto Assign to Agent                                 │
│ ☑ Show Online Status                                   │
└────────────────────────────────────────────────────────┘
```

## 📂 File Structure Created

```
BookShop/
│
├── support/                          # NEW APP
│   ├── __init__.py
│   ├── admin.py                     # ✅ Admin interface
│   ├── apps.py
│   ├── models.py                    # ✅ 5 Models
│   ├── views.py                     # ✅ 9 Views
│   ├── urls.py                      # ✅ URL routing
│   ├── tests.py
│   └── migrations/
│       └── 0001_initial.py          # ✅ Database tables
│
├── static/
│   ├── css/
│   │   └── chat-widget.css          # ✅ 350+ lines
│   └── js/
│       └── chat-widget.js           # ✅ 500+ lines
│
├── templates/
│   ├── base.html                    # ✅ Updated
│   └── support/                     # ✅ NEW
│       ├── my_conversations.html    # ✅ List view
│       └── conversation_detail.html # ✅ Detail view
│
├── media/
│   └── support/                     # ✅ NEW
│       ├── agents/                  # Agent avatars
│       └── attachments/             # File uploads
│
├── SUPPORT_CHAT_SYSTEM_GUIDE.md        # ✅ Full docs
├── SUPPORT_CHAT_QUICK_START.md         # ✅ Quick ref
├── SUPPORT_CHAT_INSTALLATION_COMPLETE.md # ✅ Summary
└── setup_support.py                    # ✅ Setup script
```

## 🗄️ Database Schema

```sql
-- 5 New Tables Created

support_supportagent
├── id (PK)
├── user_id (FK → accounts_user)
├── display_name
├── display_name_bn
├── avatar
├── is_online ⚡
├── bio
├── email
├── is_active
├── order
└── created_at

support_conversation
├── id (PK)
├── conversation_id (Unique)
├── user_id (FK → accounts_user)
├── assigned_agent_id (FK → support_supportagent)
├── subject
├── status (open/pending/resolved/closed)
├── priority (low/normal/high/urgent)
├── language (en/bn)
├── user_unread_count
├── agent_unread_count
├── last_message_at
├── created_at
└── updated_at

support_message
├── id (PK)
├── conversation_id (FK → support_conversation)
├── sender_id (FK → accounts_user)
├── is_agent
├── message_type (text/image/file/system)
├── content
├── attachment
├── attachment_name
├── is_read
├── read_at
├── created_at
└── edited_at

support_quickreply
├── id (PK)
├── title
├── title_bn
├── content
├── content_bn
├── category
├── is_active
├── order
└── created_at

support_chatsettings (Singleton)
├── id (PK = 1)
├── is_enabled
├── welcome_message
├── welcome_message_bn
├── offline_message
├── offline_message_bn
├── widget_position
├── primary_color
├── auto_assign
├── max_file_size
├── business_hours_start
├── business_hours_end
├── show_online_status
├── created_at
└── updated_at
```

## 🔄 Data Flow

### Customer Sends Message:
```
Customer Types
    ↓
JavaScript captures
    ↓
AJAX POST to /support/api/conversation/{id}/send/
    ↓
Django View validates
    ↓
Creates Message object
    ↓
Updates Conversation
    ↓
Returns JSON response
    ↓
JavaScript updates UI
    ↓
Message appears in chat
```

### Polling for New Messages:
```
Every 3 seconds:
    ↓
JavaScript makes GET request
    ↓
/support/api/conversation/{id}/messages/
    ↓
Django returns messages after last_message_id
    ↓
JavaScript checks for new messages
    ↓
If new messages found:
    ↓
Append to chat
    ↓
Update unread badge
    ↓
Play notification sound
```

### Agent Sees Conversation:
```
Admin Panel
    ↓
Conversations List
    ↓
Filter/Search
    ↓
Click conversation
    ↓
View messages inline
    ↓
Can reply (future enhancement)
    ↓
Update status/priority
    ↓
Save changes
```

## 🎨 Color Scheme

```css
/* Primary Colors */
Primary Color:     #008B8B  /* Teal/Dark Cyan */
Success (Online):  #4CAF50  /* Green */
Warning:           #FFC107  /* Amber */
Danger:            #FF4444  /* Red */
Info:              #2196F3  /* Blue */

/* Status Colors */
Open:              #28A745  /* Green */
Pending:           #FFC107  /* Yellow */
Resolved:          #17A2B8  /* Cyan */
Closed:            #6C757D  /* Gray */

/* Priority Colors */
Low:               #6C757D  /* Gray */
Normal:            #007BFF  /* Blue */
High:              #FFC107  /* Orange */
Urgent:            #DC3545  /* Red */

/* UI Elements */
Background:        #F5F5F5  /* Light Gray */
White:             #FFFFFF
Text:              #333333
Border:            #E0E0E0
Shadow:            rgba(0,0,0,0.15)
```

## 📱 Responsive Breakpoints

```css
/* Desktop */
@media (min-width: 481px) {
  .chat-window {
    width: 380px;
    height: 600px;
    border-radius: 12px;
  }
}

/* Mobile */
@media (max-width: 480px) {
  .chat-window {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }
}
```

## 🔌 API Endpoints

```
PUBLIC:
GET  /support/api/config/
     → Returns widget configuration

AUTHENTICATED:
GET  /support/api/conversation/create/
     → Get or create active conversation
     → Returns: conversation_id, status, agent info

GET  /support/api/conversation/{id}/messages/
     → Get all messages in conversation
     → Returns: array of message objects

POST /support/api/conversation/{id}/send/
     → Send text message
     → Body: { "content": "message text" }
     → Returns: message object

POST /support/api/conversation/{id}/upload/
     → Upload file attachment
     → Body: FormData with 'file'
     → Returns: message object with attachment

POST /support/api/conversation/{id}/close/
     → Close conversation
     → Returns: success status

PAGES:
GET  /support/conversations/
     → List all user's conversations

GET  /support/conversation/{id}/
     → View conversation detail page
```

## 🎯 User Journey Map

```
CUSTOMER:
Homepage → See chat button → Click button
    ↓
Chat opens → Welcome message appears
    ↓
Type message → Press Enter → Message sent
    ↓
Wait for agent reply → Polls every 3s
    ↓
Agent replies → Message appears → Continue chat
    ↓
Upload file (optional) → Send emoji (optional)
    ↓
Problem solved → Close chat → Can reopen later
    ↓
View history: Profile → Support Conversations

AGENT:
Login to admin → Navigate to Support
    ↓
Set status to "Online"
    ↓
View Conversations list → See new conversation
    ↓
Click conversation → Read messages
    ↓
Reply to customer → Update status
    ↓
Mark as Resolved → Close when done
    ↓
Set status to "Offline" → End shift
```

## 🎪 Feature Matrix

```
┌─────────────────────┬──────────┬──────────┬──────────┐
│ Feature             │ Customer │ Agent    │ Admin    │
├─────────────────────┼──────────┼──────────┼──────────┤
│ Send Messages       │    ✅    │    ❌*   │    ✅    │
│ Receive Messages    │    ✅    │    ❌*   │    ✅    │
│ Upload Files        │    ✅    │    ❌*   │    ✅    │
│ Send Emojis         │    ✅    │    ❌*   │    ❌    │
│ View History        │    ✅    │    ✅    │    ✅    │
│ Search Convos       │    ❌    │    ✅    │    ✅    │
│ Change Status       │    ❌    │    ✅    │    ✅    │
│ Set Priority        │    ❌    │    ✅    │    ✅    │
│ Assign Agent        │    ❌    │    ✅    │    ✅    │
│ Bulk Actions        │    ❌    │    ✅    │    ✅    │
│ Quick Replies       │    ❌    │    ✅    │    ✅    │
│ View Statistics     │    ❌    │    ✅    │    ✅    │
│ Configure Settings  │    ❌    │    ❌    │    ✅    │
│ Manage Agents       │    ❌    │    ❌    │    ✅    │
│ View All Convos     │    ❌    │    ✅    │    ✅    │
└─────────────────────┴──────────┴──────────┴──────────┘

* Agent live chat reply requires WebSocket (future enhancement)
```

## 📊 Initial Data

```
SUPPORT AGENTS: 1
└── admin
    ├── Display Name: admin
    ├── Display Name BN: রকমারি
    ├── Email: (from user account)
    ├── Is Online: ❌ (SET THIS TO ✅)
    ├── Avatar: (none - upload one)
    └── Order: 1

QUICK REPLIES: 5
├── 1. Shipping Info
├── 2. Payment Methods
├── 3. Return Policy
├── 4. Track Order
└── 5. Book Rental

CHAT SETTINGS: 1
├── Enabled: ✅
├── Position: Bottom Right
├── Color: #008B8B
├── Auto Assign: ✅
├── Max File Size: 5 MB
├── Show Online Status: ✅
└── Welcome Message: Set (EN & BN)
```

## ✅ Installation Checklist

```
✅ Django app 'support' created
✅ Models defined (5 models)
✅ Migrations created and applied
✅ Admin interface configured
✅ Views implemented (9 views)
✅ URLs configured
✅ Templates created (2 templates)
✅ Static files added (CSS + JS)
✅ Base template updated
✅ Settings.py updated
✅ Initial data loaded
✅ Documentation created (3 files)
✅ Development server running
```

## 🎬 What Happens When...

### User Opens Chat:
1. Widget loads configuration from API
2. Checks if user is logged in
3. Creates/retrieves conversation
4. Auto-assigns to online agent
5. Loads message history
6. Displays welcome message
7. Starts polling for new messages (3s)
8. Shows online/offline status

### User Sends Message:
1. User types in input field
2. Presses Enter or clicks send
3. JavaScript validates message
4. Sends AJAX POST request
5. Server creates Message object
6. Updates conversation timestamp
7. Increments agent unread count
8. Returns success response
9. UI updates immediately
10. Clears input field

### Agent Goes Online:
1. Admin logs into panel
2. Navigates to Support Agents
3. Edits their profile
4. Checks "Is online" box
5. Saves changes
6. Widget shows "online" status
7. New conversations auto-assign
8. Welcome message sent to customers

### File Upload:
1. User clicks paperclip icon
2. File picker opens
3. User selects file
4. JavaScript validates size (<5MB)
5. Creates FormData object
6. Sends AJAX POST with file
7. Server saves to media/support/attachments
8. Creates Message with attachment
9. Returns attachment URL
10. UI shows preview/download link

---

**🎉 Your support chat system is complete and ready!**

Just set the agent to "Online" and start chatting! 💬
