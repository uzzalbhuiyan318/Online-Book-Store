# Customer Support Chat System - Complete Guide

## 📌 Overview

A comprehensive messenger-style customer support chat system has been integrated into your BookShop application. This system provides real-time communication between customers and support agents with a modern, user-friendly interface similar to popular messaging apps.

## ✨ Features

### For Customers:
- **Floating Chat Widget**: Always accessible from any page
- **Real-time Messaging**: Instant communication with support agents
- **File Attachments**: Send images and documents (up to 5MB)
- **Emoji Support**: Express emotions with emoji picker
- **Bengali Language Support**: Full bilingual support (English & Bengali)
- **Message History**: View all past conversations
- **Online Status**: See when support agents are online
- **Unread Notifications**: Get notified of new messages
- **Responsive Design**: Works perfectly on mobile and desktop

### For Support Agents (Admin Panel):
- **Conversation Management**: View and manage all customer conversations
- **Quick Replies**: Pre-configured responses for common queries
- **Auto-Assignment**: Automatically assign conversations to available agents
- **Priority Levels**: Mark conversations as low, normal, high, or urgent
- **Status Tracking**: Open, Pending, Resolved, Closed states
- **Bulk Actions**: Perform actions on multiple conversations
- **Agent Profiles**: Customizable agent display names and avatars
- **Bengali Support**: Agent names and messages in Bengali
- **Statistics**: Track unread messages and conversation metrics

## 📂 Project Structure

```
BookShop/
├── support/                    # New Django app
│   ├── models.py              # Database models
│   ├── views.py               # API endpoints and views
│   ├── admin.py               # Admin panel customization
│   ├── urls.py                # URL routing
│   └── migrations/
│       └── 0001_initial.py
├── static/
│   ├── css/
│   │   └── chat-widget.css    # Chat widget styles
│   └── js/
│       └── chat-widget.js     # Chat widget functionality
├── templates/
│   ├── base.html              # Updated with chat widget
│   └── support/
│       ├── my_conversations.html
│       └── conversation_detail.html
└── setup_support.py           # Setup script
```

## 🗄️ Database Models

### 1. **SupportAgent**
- Represents support agents
- Fields: display_name, display_name_bn, avatar, is_online, bio, email, etc.
- One-to-one with User model

### 2. **Conversation**
- Represents a chat conversation
- Fields: conversation_id, user, assigned_agent, status, priority, language
- Status: open, pending, resolved, closed
- Priority: low, normal, high, urgent

### 3. **Message**
- Individual messages in conversations
- Fields: conversation, sender, is_agent, content, attachment, is_read
- Message types: text, image, file, system

### 4. **QuickReply**
- Pre-configured quick responses
- Fields: title, content (both English and Bengali)
- Categories: Shipping, Payment, Returns, Orders, Rentals

### 5. **ChatSettings**
- Global chat widget configuration
- Fields: welcome_message, primary_color, widget_position, etc.
- Singleton pattern (only one instance)

## 🎨 Chat Widget UI

### Chat Button
- Fixed position (bottom-right or bottom-left)
- Teal/turquoise color (#008B8B) - customizable
- Shows unread message count badge
- Floating animation on hover

### Chat Window
- 380px × 600px (responsive on mobile)
- Header with agent info and online status
- Scrollable message area
- Input area with emoji and attachment buttons
- Modern, clean design matching the screenshot

### Message Styles
- Agent messages: White bubble, left-aligned
- User messages: Teal bubble, right-aligned
- System messages: Centered, blue background
- Timestamps and read receipts
- Support for images and file attachments

## 🔧 Configuration

### Chat Settings (Admin Panel → Chat Settings)

**General Settings:**
- **Enable Chat Widget**: Turn chat on/off
- **Widget Position**: bottom-right or bottom-left
- **Primary Color**: Hex color code (default: #008B8B)
- **Show Online Status**: Display agent online status

**Messages:**
- **Welcome Message (EN)**: "Hello! How can we help you today?"
- **Welcome Message (BN)**: "আসসালামু আলাইকুম, রকমারি উটকসে স আপনাকে স্বাগতম..."
- **Offline Message (EN/BN)**: Messages when agents are offline

**Assignment & Limits:**
- **Auto Assign**: Automatically assign to available agents
- **Max File Size**: 5MB (default)

**Business Hours:**
- **Start Time**: 09:00
- **End Time**: 18:00

## 👥 Support Agent Management

### Creating Support Agents

1. **Via Admin Panel:**
   - Go to Admin Panel → Support → Support Agents → Add
   - Select a staff user
   - Enter display names (English & Bengali)
   - Upload avatar (optional)
   - Set as online/offline
   - Add bio (optional)

2. **Via Setup Script:**
   - Run: `python setup_support.py`
   - Automatically creates agents for all staff users

### Agent Status

**Online Status:**
- Green dot indicator
- Shows "Support is online"
- Customers can see agent availability
- Set in admin panel: `is_online` checkbox

**Offline Status:**
- Gray dot indicator
- Shows offline message
- Customers can still leave messages

## 📊 Admin Panel Features

### Conversation Management

**List View:**
- Conversation ID with clickable link
- User information
- Assigned agent
- Status badge (color-coded)
- Priority badge
- Unread message counts
- Last message timestamp

**Detail View:**
- Full conversation thread
- Inline message display
- Conversation metadata
- Assignment controls
- Status and priority management

**Bulk Actions:**
- Mark as Resolved
- Mark as Closed
- Assign to Me
- Mark as High Priority

**Filters:**
- By status (open, pending, resolved, closed)
- By priority level
- By language (en, bn)
- By assigned agent
- By date created

### Message Administration

**Features:**
- View all messages across conversations
- Filter by type, sender, read status
- Search by content
- View attachments inline
- Track read receipts

### Quick Replies

**Default Quick Replies:**
1. **Shipping Info** - Delivery timeframes and costs
2. **Payment Methods** - Accepted payment options
3. **Return Policy** - 7-day return process
4. **Track Order** - Order tracking information
5. **Book Rental** - Rental service details

**Usage:**
- Agents can quickly insert common responses
- Available in both English and Bengali
- Customizable categories
- Sortable by order

## 🌐 API Endpoints

### Public Endpoints:
```
GET  /support/api/config/                     # Get widget configuration
```

### Authenticated Endpoints:
```
GET  /support/api/conversation/create/        # Get or create conversation
GET  /support/api/conversation/{id}/messages/ # Get messages
POST /support/api/conversation/{id}/send/     # Send message
POST /support/api/conversation/{id}/upload/   # Upload file
POST /support/api/conversation/{id}/close/    # Close conversation
```

### Frontend Pages:
```
GET  /support/conversations/                  # List all conversations
GET  /support/conversation/{id}/              # View conversation detail
```

## 💻 Usage Examples

### For Customers:

1. **Start Chat:**
   - Click floating chat button (bottom-right)
   - Widget opens with welcome message
   - Type message and hit Enter or click send

2. **Send Files:**
   - Click paperclip icon
   - Select image/document (max 5MB)
   - File uploads automatically

3. **Use Emojis:**
   - Click emoji button
   - Select from popular emojis
   - Emoji added to message

4. **View History:**
   - Go to Profile → Support Conversations
   - View all past conversations
   - Click to open and continue

### For Agents:

1. **Go Online:**
   - Admin Panel → Support → Support Agents
   - Find your agent profile
   - Check "Is online" box
   - Save

2. **View Conversations:**
   - Admin Panel → Support → Conversations
   - See all active conversations
   - Filter by status/priority

3. **Reply to Customer:**
   - Click on conversation
   - Scroll to messages section
   - Type reply in admin interface
   - (Note: Real-time agent reply requires additional setup)

4. **Use Quick Replies:**
   - Admin Panel → Support → Quick Replies
   - Create common responses
   - Copy and use in conversations

5. **Manage Status:**
   - Change status to "Resolved" when issue fixed
   - Change to "Closed" to end conversation
   - Use priority to highlight urgent issues

## 🎨 Customization

### Change Widget Color:
1. Admin Panel → Chat Settings
2. Edit "Primary Color" field
3. Enter hex color (e.g., #FF5733)
4. Save - widget updates instantly

### Change Widget Position:
1. Admin Panel → Chat Settings
2. Change "Widget Position" dropdown
3. Choose: bottom-right or bottom-left
4. Save

### Customize Welcome Message:
1. Admin Panel → Chat Settings
2. Edit "Welcome Message" (English)
3. Edit "Welcome Message Bn" (Bengali)
4. Save

### Add Support Agent Avatar:
1. Admin Panel → Support → Support Agents
2. Edit agent profile
3. Upload image in "Avatar" field
4. Save - appears in chat header

## 🔐 Security Features

- **CSRF Protection**: All POST requests protected
- **Authentication Required**: Chat only for logged-in users
- **File Validation**: Only allowed file types
- **Size Limits**: Configurable max file size
- **XSS Protection**: HTML escaping in messages
- **SQL Injection Protection**: Django ORM parameterized queries

## 📱 Responsive Design

- **Desktop**: Full 380×600px chat window
- **Mobile**: Full-screen chat interface
- **Tablet**: Optimized layout
- **Touch-friendly**: Large buttons and inputs

## 🌍 Bengali Language Support

The system fully supports Bengali (বাংলা):

- Agent display names in Bengali
- Welcome and offline messages in Bengali
- Quick replies in Bengali
- Automatic language detection
- Bengali font rendering (Kalpurush, SolaimanLipi, Noto Sans Bengali)

## 🚀 Getting Started

### 1. Initial Setup (Already Done):
```bash
# Migrations already applied
# Setup script already run
```

### 2. Configure Support:
```bash
# Go to admin panel
http://localhost:8000/admin/

# Navigate to Support section
# Configure Chat Settings
# Create/Update Support Agents
# Add Quick Replies
```

### 3. Set Agent Online:
```
Admin Panel → Support → Support Agents
→ Select your agent
→ Check "Is online"
→ Save
```

### 4. Test Chat:
```
1. Open website as customer
2. Click chat button (bottom-right)
3. Send test message
4. Check admin panel for conversation
```

## 🐛 Troubleshooting

### Chat Widget Not Appearing:
- Check Chat Settings → "Enable Chat Widget" is checked
- Verify CSS/JS files are loaded (check browser console)
- Clear browser cache
- Check if logged in (required for chat)

### Messages Not Sending:
- Check browser console for errors
- Verify CSRF token is present
- Ensure user is authenticated
- Check server logs for errors

### Agent Not Online:
- Admin Panel → Support Agents
- Find agent profile
- Ensure "Is online" checkbox is checked
- Save changes

### File Upload Failing:
- Check file size (must be under 5MB)
- Verify file type is allowed
- Check MEDIA_ROOT settings
- Ensure media directory has write permissions

## 📈 Performance Optimization

- **Message Polling**: Updates every 3 seconds
- **Lazy Loading**: Only loads messages when chat opens
- **Image Optimization**: Consider compressing uploaded images
- **Database Indexing**: conversation_id, user, created_at indexed
- **Caching**: Consider caching chat settings

## 🔄 Future Enhancements

Possible improvements:
1. **WebSocket Support**: Real-time bi-directional communication
2. **Typing Indicators**: Show when agent is typing
3. **Push Notifications**: Browser notifications for new messages
4. **Voice Messages**: Audio message support
5. **Video Chat**: Integrate video calling
6. **Chat Bot**: AI-powered automatic responses
7. **Analytics Dashboard**: Chat metrics and KPIs
8. **Mobile App**: Native iOS/Android apps
9. **Multi-language**: Support for more languages
10. **Screen Sharing**: Help customers with visual guidance

## 📞 Support

For issues or questions about the chat system:
1. Check this documentation
2. Review admin panel configuration
3. Check browser console for errors
4. Review Django logs
5. Test with different browsers

## 🎉 Success!

Your BookShop now has a professional customer support chat system! Customers can easily reach out for help, and your support team can efficiently manage all conversations from the admin panel.

**Key Benefits:**
✅ Improved customer satisfaction
✅ Faster response times
✅ Better support organization
✅ Reduced email/phone support load
✅ Professional appearance
✅ Bengali language support
✅ Mobile-friendly interface
✅ Easy to manage

---

**Created:** November 9, 2025
**Version:** 1.0
**Django:** 4.2.7
**Database:** MySQL
