// Chat Widget JavaScript
class ChatWidget {
    constructor() {
        this.config = null;
        this.conversation = null;
        this.isOpen = false;
        this.unreadCount = 0;
        this.messagePollingInterval = null;
        this.lastMessageId = 0;
        
        this.init();
    }
    
    async init() {
        console.log('Initializing chat widget...');
        
        // Load configuration
        await this.loadConfig();
        
        console.log('Config loaded, enabled:', this.config?.enabled);
        
        // Create widget HTML
        this.createWidget();
        
        // Bind events
        this.bindEvents();
        
        console.log('Chat widget initialization complete');
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/support/api/config/');
            this.config = await response.json();
            console.log('Chat config loaded:', this.config);
        } catch (error) {
            console.error('Failed to load chat config:', error);
            this.config = { 
                enabled: false,
                welcome_message: 'Hello! How can we help you today?'
            };
        }
    }
    
    createWidget() {
        if (!this.config.enabled) {
            console.log('Chat widget is disabled in config');
            return;
        }
        
        console.log('Creating chat widget...');
        
        const widgetHTML = `
            <div class="chat-widget ${this.config.position}">
                <div class="chat-window" id="chatWindow">
                    <div class="chat-header">
                        <div class="chat-header-info">
                            <div class="chat-avatar-placeholder">
                                <i class="fas fa-headset"></i>
                            </div>
                            <div class="chat-agent-info">
                                <h6 id="chatAgentName">Customer Support</h6>
                                <div class="chat-status">
                                    <span class="status-dot"></span>
                                    <span id="chatStatus">Support is online</span>
                                </div>
                            </div>
                        </div>
                        <div class="chat-header-actions">
                            <button id="chatMinimize" title="Minimize">
                                <i class="fas fa-minus"></i>
                            </button>
                            <button id="chatClose" title="Close">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="chat-messages" id="chatMessages">
                        <div class="chat-loading">
                            <div class="spinner"></div>
                        </div>
                    </div>
                    
                    <div class="chat-input-area">
                        <div class="chat-input-container">
                            <textarea 
                                class="chat-input" 
                                id="chatInput" 
                                placeholder="Type your message..."
                                rows="1"
                            ></textarea>
                            <div class="chat-input-buttons">
                                <button id="emojiButton" title="Emoji">
                                    <i class="far fa-smile"></i>
                                </button>
                                <button id="attachButton" title="Attach file">
                                    <i class="fas fa-paperclip"></i>
                                </button>
                                <button id="sendButton" class="send-button" title="Send" disabled>
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                        <input type="file" id="chatFileInput" class="chat-file-input" accept="image/*,.pdf,.doc,.docx,.txt">
                    </div>
                </div>
                
                <button class="chat-button" id="chatToggle">
                    <i class="fas fa-comments"></i>
                    <span class="unread-badge" id="unreadBadge" style="display: none;">0</span>
                </button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
        
        // Apply custom color
        if (this.config.primary_color) {
            document.documentElement.style.setProperty('--chat-primary-color', this.config.primary_color);
            const style = document.createElement('style');
            style.textContent = `
                .chat-button, .chat-header { background: ${this.config.primary_color} !important; }
                .message.user-message .message-bubble { background: ${this.config.primary_color} !important; }
                .chat-input:focus { border-color: ${this.config.primary_color} !important; }
                .send-button { background: ${this.config.primary_color} !important; }
            `;
            document.head.appendChild(style);
        }
    }
    
    bindEvents() {
        const chatToggle = document.getElementById('chatToggle');
        const chatMinimize = document.getElementById('chatMinimize');
        const chatClose = document.getElementById('chatClose');
        const sendButton = document.getElementById('sendButton');
        const chatInput = document.getElementById('chatInput');
        const attachButton = document.getElementById('attachButton');
        const chatFileInput = document.getElementById('chatFileInput');
        const emojiButton = document.getElementById('emojiButton');
        
        if (chatToggle) {
            chatToggle.addEventListener('click', () => this.toggleChat());
        }
        
        if (chatMinimize) {
            chatMinimize.addEventListener('click', () => this.closeChat());
        }
        
        if (chatClose) {
            chatClose.addEventListener('click', () => this.closeChat());
        }
        
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (chatInput) {
            chatInput.addEventListener('input', (e) => {
                this.autoResizeInput(e.target);
                sendButton.disabled = !e.target.value.trim();
            });
            
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        if (attachButton && chatFileInput) {
            attachButton.addEventListener('click', () => chatFileInput.click());
            chatFileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        if (emojiButton) {
            emojiButton.addEventListener('click', () => this.toggleEmojiPicker());
        }
    }
    
    autoResizeInput(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    }
    
    async toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            await this.openChat();
        }
    }
    
    async openChat() {
        console.log('Opening chat widget...');
        const chatWindow = document.getElementById('chatWindow');
        if (!chatWindow) {
            console.error('Chat window element not found');
            return;
        }
        
        chatWindow.classList.add('open');
        this.isOpen = true;
        console.log('Chat window opened');
        
        // Initialize conversation
        if (!this.conversation) {
            await this.initConversation();
        } else {
            console.log('Conversation already exists:', this.conversation.conversation_id);
        }
        
        // Reset unread count
        this.unreadCount = 0;
        this.updateUnreadBadge();
        
        // Focus input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) chatInput.focus();
    }
    
    closeChat() {
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.classList.remove('open');
        }
        this.isOpen = false;
        
        // Stop polling
        if (this.messagePollingInterval) {
            clearInterval(this.messagePollingInterval);
            this.messagePollingInterval = null;
        }
    }
    
    async initConversation() {
        console.log('Initializing conversation...');
        try {
            const response = await fetch('/support/api/conversation/create/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            console.log('Conversation response status:', response.status);
            
            if (!response.ok) {
                // User not logged in
                console.log('User not logged in or error occurred');
                this.showLoginMessage();
                return;
            }
            
            this.conversation = await response.json();
            console.log('Conversation created/loaded:', this.conversation);
            
            // Update agent info
            if (this.conversation.agent) {
                this.updateAgentInfo(this.conversation.agent);
            }
            
            // Load messages
            await this.loadMessages();
            
            // Start polling for new messages
            this.startMessagePolling();
            
        } catch (error) {
            console.error('Failed to initialize conversation:', error);
            this.showErrorMessage('Failed to connect. Please try again.');
        }
    }
    
    updateAgentInfo(agent) {
        const agentNameEl = document.getElementById('chatAgentName');
        const agentAvatar = document.querySelector('.chat-avatar-placeholder');
        
        if (agentNameEl && agent.name) {
            // Use Bengali name if available and language is Bengali
            const lang = document.documentElement.lang || 'en';
            agentNameEl.textContent = (lang === 'bn' && agent.name_bn) ? agent.name_bn : agent.name;
        }
        
        if (agentAvatar && agent.avatar) {
            agentAvatar.innerHTML = `<img src="${agent.avatar}" alt="${agent.name}" class="chat-avatar">`;
        }
        
        // Update online status
        const statusEl = document.getElementById('chatStatus');
        if (statusEl) {
            statusEl.textContent = agent.is_online ? 'Support is online' : 'Support is offline';
        }
    }
    
    async loadMessages() {
        if (!this.conversation) {
            console.log('No conversation, skipping message load');
            return;
        }
        
        console.log('Loading messages for conversation:', this.conversation.conversation_id);
        
        try {
            const response = await fetch(`/support/api/conversation/${this.conversation.conversation_id}/messages/`);
            console.log('Messages response status:', response.status);
            
            const data = await response.json();
            console.log('Messages data:', data);
            
            this.renderMessages(data.messages);
            
            // Track last message ID
            if (data.messages.length > 0) {
                this.lastMessageId = data.messages[data.messages.length - 1].id;
            }
            
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    }
    
    renderMessages(messages) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        console.log('Rendering messages:', messages.length, 'messages');
        chatMessages.innerHTML = '';
        
        if (messages.length === 0) {
            const welcomeMsg = this.config?.welcome_message || 'Hello! How can we help you today?';
            console.log('No messages, showing welcome:', welcomeMsg);
            chatMessages.innerHTML = `
                <div class="message system-message">
                    <div class="message-bubble">${welcomeMsg}</div>
                </div>
            `;
            return;
        }
        
        messages.forEach(msg => {
            this.appendMessage(msg);
        });
        
        this.scrollToBottom();
    }
    
    appendMessage(msg) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageClass = msg.is_agent ? 'agent-message' : 'user-message';
        const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let avatarHTML = '';
        if (msg.is_agent) {
            avatarHTML = msg.sender_avatar 
                ? `<img src="${msg.sender_avatar}" alt="${msg.sender_name}" class="message-avatar">`
                : `<div class="message-avatar-placeholder"><i class="fas fa-user-tie"></i></div>`;
        } else {
            avatarHTML = msg.sender_avatar 
                ? `<img src="${msg.sender_avatar}" alt="${msg.sender_name}" class="message-avatar">`
                : `<div class="message-avatar-placeholder">${msg.sender_name.charAt(0)}</div>`;
        }
        
        let attachmentHTML = '';
        if (msg.attachment) {
            if (msg.message_type === 'image') {
                attachmentHTML = `
                    <div class="message-attachment">
                        <img src="${msg.attachment}" alt="${msg.attachment_name}" onclick="window.open('${msg.attachment}', '_blank')">
                    </div>
                `;
            } else {
                attachmentHTML = `
                    <div class="message-attachment">
                        <a href="${msg.attachment}" target="_blank" download>
                            <i class="fas fa-file"></i>
                            <span>${msg.attachment_name}</span>
                        </a>
                    </div>
                `;
            }
        }
        
        const messageHTML = `
            <div class="message ${messageClass}" data-message-id="${msg.id}">
                ${avatarHTML}
                <div class="message-content">
                    <div class="message-bubble">${this.escapeHtml(msg.content)}</div>
                    ${attachmentHTML}
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;
        
        chatMessages.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }
    
    async sendMessage() {
        if (!this.conversation) return;
        
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        
        if (!chatInput || !chatInput.value.trim()) return;
        
        const content = chatInput.value.trim();
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendButton.disabled = true;
        
        try {
            const response = await fetch(`/support/api/conversation/${this.conversation.conversation_id}/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ content })
            });
            
            if (response.ok) {
                // Message sent, reload messages
                await this.loadMessages();
            } else {
                alert('Failed to send message. Please try again.');
                chatInput.value = content;
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            alert('Failed to send message. Please try again.');
            chatInput.value = content;
        }
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file || !this.conversation) return;
        
        // Check file size
        if (file.size > this.config.max_file_size) {
            alert(`File size must be less than ${this.config.max_file_size / (1024 * 1024)}MB`);
            event.target.value = '';
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('content', `Sent ${file.name}`);
        
        try {
            const response = await fetch(`/support/api/conversation/${this.conversation.conversation_id}/upload/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: formData
            });
            
            if (response.ok) {
                await this.loadMessages();
            } else {
                alert('Failed to upload file. Please try again.');
            }
        } catch (error) {
            console.error('Failed to upload file:', error);
            alert('Failed to upload file. Please try again.');
        } finally {
            event.target.value = '';
        }
    }
    
    startMessagePolling() {
        if (this.messagePollingInterval) return;
        
        this.messagePollingInterval = setInterval(async () => {
            if (this.conversation && this.isOpen) {
                await this.checkNewMessages();
            }
        }, 3000); // Poll every 3 seconds
    }
    
    async checkNewMessages() {
        if (!this.conversation) return;
        
        try {
            const response = await fetch(`/support/api/conversation/${this.conversation.conversation_id}/messages/`);
            const data = await response.json();
            
            // Check if there are new messages
            const newMessages = data.messages.filter(msg => msg.id > this.lastMessageId);
            
            if (newMessages.length > 0) {
                newMessages.forEach(msg => {
                    this.appendMessage(msg);
                    if (!this.isOpen && msg.is_agent) {
                        this.unreadCount++;
                    }
                });
                
                this.lastMessageId = data.messages[data.messages.length - 1].id;
                this.updateUnreadBadge();
                
                // Play notification sound (optional)
                this.playNotificationSound();
            }
        } catch (error) {
            console.error('Failed to check new messages:', error);
        }
    }
    
    updateUnreadBadge() {
        const badge = document.getElementById('unreadBadge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    playNotificationSound() {
        // Optional: play a subtle notification sound
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIGGm67OmeUAwPUKbj8LdjHQU2kdLtyHknBCR2xPDcjj4IFGCz6OmiUhIMRp7f8rtvIQUpf832z4k4CBlpu+vnnVIMD0+l4+6yaB4FN4/S7MZ4JwQjdMPv24s+BxJasOXlnU4LDESc3ey5aSIEKHnG8NKEPAcZZ7rp5JdSCw5Mouzqr2MfBTWL0OrDdSYEInLB7tiIOQcTWq7l45lRCwxFnNvqtmkcBSp4xO/PgjsHF2S36OOXUgsOTKDr6atsHwU0h87qwnQmBSJ1wevYhzgGE1qt5OOYUQoMRJrZ6rVpGgUqeMPuzoI7BxdkvOjil1ILDkyg7Omtax4FNIbO6cJzJgQjdcHr2Ic3BxNYrOTjmFEJDUSa2eq0aRoFKnjE787DOwYVY7vn4pdRCg5Ln+vpr2sdBTWGzunCcyYEI3XB69iHNwcSWKzl45hQCgxEmtnqtGkaBS14w+7Owjp/+7AAAAMH0P4wAAAP8AHz4AAPP/w8P/w8P8P/48B4P/48B4A==');
            audio.volume = 0.3;
            audio.play().catch(() => {}); // Ignore if audio play fails
        } catch (error) {
            // Ignore audio errors
        }
    }
    
    toggleEmojiPicker() {
        // Simple emoji implementation
        const emojis = ['😊', '😂', '❤️', '👍', '🙏', '😢', '😍', '🎉', '👏', '🙌'];
        const chatInput = document.getElementById('chatInput');
        
        // Create a simple emoji menu
        let emojiMenu = document.querySelector('.emoji-picker');
        
        if (emojiMenu) {
            emojiMenu.remove();
        } else {
            emojiMenu = document.createElement('div');
            emojiMenu.className = 'emoji-picker show';
            
            emojis.forEach(emoji => {
                const span = document.createElement('span');
                span.textContent = emoji;
                span.onclick = () => {
                    chatInput.value += emoji;
                    chatInput.focus();
                    emojiMenu.remove();
                    document.getElementById('sendButton').disabled = false;
                };
                emojiMenu.appendChild(span);
            });
            
            document.querySelector('.chat-widget').appendChild(emojiMenu);
            
            // Close on outside click
            setTimeout(() => {
                document.addEventListener('click', function closeEmoji(e) {
                    if (!e.target.closest('.emoji-picker') && !e.target.closest('#emojiButton')) {
                        emojiMenu.remove();
                        document.removeEventListener('click', closeEmoji);
                    }
                });
            }, 100);
        }
    }
    
    showLoginMessage() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message system-message">
                    <div class="message-bubble">
                        Please <a href="/accounts/login/">login</a> to start a conversation with support.
                    </div>
                </div>
            `;
        }
    }
    
    showErrorMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message system-message">
                    <div class="message-bubble">${message}</div>
                </div>
            `;
        }
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize chat widget when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ChatWidget();
    });
} else {
    new ChatWidget();
}
