/**
 * Enhanced Chat Client for MateHub
 * Handles chat functionality with configurable IDs and model settings
 */
class ChatClient {
    constructor() {
        this.apiService = new ApiService();
        this.config = this.loadConfig();
        this.conversationHistory = [];
        this.isWaitingForResponse = false;
        this.currentTaskId = null;
        this.chatHistoryLoaded = false;
        this.nextCursor = null;  // Cursor for loading older messages
        this.prevCursor = null;  // Cursor for loading newer messages
        this.hasMoreHistory = false;
        this.isLoadingHistory = false;
        
        // Typewriter effect settings
        this.typewriterSpeed = 25;
        this.enableTypewriter = true;
        
        this.initializeElements();
        this.attachEventListeners();
        this.updateConfigDisplay();
        this.checkServerHealth();
        
        // Load chat history after initialization
        this.loadChatHistory();
    }

    /**
     * Load configuration from localStorage or use defaults
     */
    loadConfig() {
        const defaultConfig = {
            userId: 1,
            characterId: 1,
            storyId: 1,
            phraseId: 1,
            model: 'llama3.2'
        };

        try {
            const saved = localStorage.getItem('matehub-config');
            return saved ? { ...defaultConfig, ...JSON.parse(saved) } : defaultConfig;
        } catch (error) {
            console.warn('Failed to load config from localStorage:', error);
            return defaultConfig;
        }
    }

    /**
     * Save configuration to localStorage
     */
    saveConfig() {
        try {
            localStorage.setItem('matehub-config', JSON.stringify(this.config));
        } catch (error) {
            console.warn('Failed to save config to localStorage:', error);
        }
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Chat elements
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.loadMoreContainer = document.getElementById('loadMoreContainer');
        this.loadMoreBtn = document.getElementById('loadMoreBtn');
        this.scrollLoadingIndicator = document.getElementById('scrollLoadingIndicator');

        // Config elements
        this.modelSelect = document.getElementById('modelSelect');

        // ID display elements
        this.headerUserId = document.getElementById('headerUserId');
        this.headerCharacterId = document.getElementById('headerCharacterId');
        this.headerStoryId = document.getElementById('headerStoryId');

        // Set initial values
        if (this.modelSelect) this.modelSelect.value = this.config.model;
        
        // Load available models
        this.loadAvailableModels();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Chat form submission
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // Model selection
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', (e) => {
                this.config.model = e.target.value;
                this.saveConfig();
                console.log('Model changed to:', e.target.value);
            });
        }

        // Load more button
        if (this.loadMoreBtn) {
            this.loadMoreBtn.addEventListener('click', () => {
                this.loadMoreHistory();
            });
        }

        // Scroll event for loading older messages
        if (this.chatMessages) {
            this.chatMessages.addEventListener('scroll', () => {
                this.handleScroll();
            });
        }

        // Keyboard shortcuts
        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Window focus events
        window.addEventListener('focus', () => this.checkServerHealth());
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) this.checkServerHealth();
        });
    }

    /**
     * Update configuration display in header
     */
    updateConfigDisplay() {
        if (this.headerUserId) this.headerUserId.textContent = this.config.userId;
        if (this.headerCharacterId) this.headerCharacterId.textContent = this.config.characterId;
        if (this.headerStoryId) this.headerStoryId.textContent = this.config.storyId;
    }

    /**
     * Update ID configuration
     */
    updateId(type, value) {
        const numValue = parseInt(value);
        if (isNaN(numValue) || numValue < 1) {
            this.showError('ID must be a positive number');
            return false;
        }

        const oldUserId = this.config.userId;
        const oldStoryId = this.config.storyId;

        switch (type) {
            case 'user':
                this.config.userId = numValue;
                break;
            case 'character':
                this.config.characterId = numValue;
                break;
            case 'story':
                this.config.storyId = numValue;
                break;
            case 'phrase':
                this.config.phraseId = numValue;
                break;
            default:
                this.showError('Invalid ID type');
                return false;
        }

        this.saveConfig();
        this.updateConfigDisplay();
        this.showSuccess(`${type.charAt(0).toUpperCase() + type.slice(1)} ID updated to ${numValue}`);
        
        // Reload chat history if user or story changed
        if ((type === 'user' && oldUserId !== numValue) || 
            (type === 'story' && oldStoryId !== numValue)) {
            this.reloadChatHistory();
        }
        
        return true;
    }

    /**
     * Send chat message - optimized to avoid unnecessary chat/history calls
     */
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isWaitingForResponse) return;

        try {
            // Validate message
            this.apiService.validateChatRequest({ message });

            // Check if user is at bottom of chat (to avoid unnecessary history reload)
            const isAtBottom = this.isScrolledToBottom();
            console.log(`📍 User at bottom before sending: ${isAtBottom}`);

            // Disable input
            this.setInputState(false);
            this.isWaitingForResponse = true;

            // Add user message to UI (always scroll for user's own message)
            this.addMessage(message, 'sent', false, null, true);
            this.conversationHistory.push({ type: 'user', message });
            this.messageInput.value = '';

            // Show typing indicator
            this.showTypingIndicator();

            // Send to API
            const chatRequest = {
                message,
                userId: this.config.userId,
                characterId: this.config.characterId,
                storyId: this.config.storyId,
                phraseId: this.config.phraseId,
                model: this.config.model
            };

            const response = await this.apiService.sendChatMessage(chatRequest);
            this.currentStoryChatHistoryId = response.story_chat_history_id;
            this.updateStatus('connected', 'AI is thinking...');

            // Poll for chat history status instead of task result
            const result = await this.apiService.pollChatHistoryStatus(response.story_chat_history_id, {
                onProgress: (data, attempts) => {
                    console.log(`Polling attempt ${attempts}:`, data.status);
                    
                    // Update status based on polling progress
                    if (data.status === 'processing') {
                        this.updateStatus('processing', 'AI is processing...');
                    } else if (data.status === 'pending') {
                        this.updateStatus('connecting', 'AI is thinking...');
                    } else {
                        this.updateStatus('connected', `AI status: ${data.status}`);
                    }
                }
            });

            // Handle successful response
            this.hideTypingIndicator();
            
            // Extract AI response from the completed result
            let aiResponse = 'No response received';
            
            if (result.chatHistory && result.chatHistory.contents) {
                // Use the contents from the full chat history
                aiResponse = result.chatHistory.contents;
            } else if (result.response) {
                // Fallback to response field from status
                aiResponse = result.response;
            } else if (result.contents) {
                // Another fallback
                aiResponse = result.contents;
            }
            
            console.log('Final AI response:', aiResponse);
            
            // Add AI response with typewriter effect
            // Only force scroll if user was at bottom when they sent the message
            this.addMessageWithTypewriter(aiResponse, 'received', false, null, isAtBottom);
            this.conversationHistory.push({ type: 'assistant', message: aiResponse });
            
            console.log(`📍 AI response added with forceScroll: ${isAtBottom}`);
            
            this.updateStatus('connected', 'Connected');

        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.showError(this.apiService.formatError(error));
            this.updateStatus('error', 'Error');
        } finally {
            this.isWaitingForResponse = false;
            this.setInputState(true);
            this.messageInput.focus();
        }
    }

    /**
     * Check server health
     */
    async checkServerHealth() {
        this.updateStatus('connecting', 'Connecting...');
        
        try {
            await this.apiService.checkLlmHealth();
            this.updateStatus('connected', 'Connected');
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus('error', 'Server Offline');
        }
    }

    /**
     * Load available models from API
     */
    async loadAvailableModels() {
        if (!this.modelSelect) return;

        try {
            this.modelSelect.innerHTML = '<option value="">Loading models...</option>';
            
            const models = await this.apiService.getAvailableModels();
            console.log('Loaded models:', models);
            
            // Clear loading option
            this.modelSelect.innerHTML = '';
            
            if (models && Array.isArray(models) && models.length > 0) {
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    this.modelSelect.appendChild(option);
                });
                
                // Set saved model if it exists in the list
                if (models.includes(this.config.model)) {
                    this.modelSelect.value = this.config.model;
                } else {
                    // Set first model as default if saved model not found
                    this.config.model = models[0];
                    this.modelSelect.value = models[0];
                    this.saveConfig();
                }
            } else {
                // Fallback if no models returned
                const option = document.createElement('option');
                option.value = 'llama3.2';
                option.textContent = 'llama3.2 (default)';
                this.modelSelect.appendChild(option);
                this.modelSelect.value = 'llama3.2';
                this.config.model = 'llama3.2';
                this.saveConfig();
            }
            
        } catch (error) {
            console.error('Failed to load models:', error);
            
            // Fallback to default model on error
            this.modelSelect.innerHTML = '';
            const option = document.createElement('option');
            option.value = 'llama3.2';
            option.textContent = 'llama3.2 (default)';
            this.modelSelect.appendChild(option);
            this.modelSelect.value = 'llama3.2';
            this.config.model = 'llama3.2';
            this.saveConfig();
        }
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.textContent = 'AI is thinking...';
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    /**
     * Add message to chat - with smart scrolling
     */
    addMessage(content, type, isError = false, messageId = null, forceScroll = false) {
        const wasAtBottom = this.isScrolledToBottom();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (isError) {
            messageDiv.style.backgroundColor = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.border = '1px solid #f5c6cb';
        }

        const timeString = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        // Parse content for situation/dialogue format
        const parsed = this.parseMessageContent(content);
        
        let messageContentHtml;
        if (parsed.hasSituation) {
            messageContentHtml = `
                <div class="message-situation-content">${this.escapeHtml(parsed.situation)}</div>
                <div class="message-dialogue-content">${this.escapeHtml(parsed.dialogue)}</div>
            `;
        } else {
            messageContentHtml = this.escapeHtml(parsed.content);
        }

        // Create message ID display if available
        const messageIdHtml = messageId ? `<div class="message-id">ID: ${messageId}</div>` : '';

        messageDiv.innerHTML = `
            <div class="message-content">${messageContentHtml}</div>
            <div class="message-footer">
                <div class="message-time">${timeString}</div>
                ${messageIdHtml}
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        
        // Only scroll if user was at bottom or force scroll is requested
        if (wasAtBottom || forceScroll) {
            this.scrollToBottom();
            console.log(`📍 Scrolled to bottom (wasAtBottom: ${wasAtBottom}, forceScroll: ${forceScroll})`);
        } else {
            console.log('📍 User not at bottom - not auto-scrolling');
        }
    }

    /**
     * Add message with typewriter effect - with smart scrolling
     */
    addMessageWithTypewriter(content, type, isError = false, messageId = null, forceScroll = false) {
        if (!this.enableTypewriter) {
            this.addMessage(content, type, isError, messageId, forceScroll);
            return;
        }

        const wasAtBottom = this.isScrolledToBottom();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (isError) {
            messageDiv.style.backgroundColor = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.border = '1px solid #f5c6cb';
        }

        const timeString = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageFooter = document.createElement('div');
        messageFooter.className = 'message-footer';
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = timeString;
        
        messageFooter.appendChild(messageTime);
        
        // Add message ID if available
        if (messageId) {
            const messageIdDiv = document.createElement('div');
            messageIdDiv.className = 'message-id';
            messageIdDiv.textContent = `ID: ${messageId}`;
            messageFooter.appendChild(messageIdDiv);
        }

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageFooter);
        this.chatMessages.appendChild(messageDiv);
        
        // Only scroll if user was at bottom or force scroll is requested
        if (wasAtBottom || forceScroll) {
            this.scrollToBottom();
            console.log(`📍 Scrolled to bottom for typewriter (wasAtBottom: ${wasAtBottom}, forceScroll: ${forceScroll})`);
        } else {
            console.log('📍 User not at bottom - not auto-scrolling for typewriter');
        }

        // Parse content for situation/dialogue format
        const parsed = this.parseMessageContent(content);
        
        if (parsed.hasSituation) {
            // Create situation content (grey italic)
            const situationContent = document.createElement('div');
            situationContent.className = 'message-situation-content';
            messageContent.appendChild(situationContent);
            
            // Create dialogue content (normal)
            const dialogueContent = document.createElement('div');
            dialogueContent.className = 'message-dialogue-content';
            messageContent.appendChild(dialogueContent);
            
            // Typewriter effect: situation first, then dialogue
            this.typewriterEffect(situationContent, parsed.situation, () => {
                this.typewriterEffect(dialogueContent, parsed.dialogue);
            });
        } else {
            // Regular typewriter effect
            this.typewriterEffect(messageContent, parsed.content);
        }
    }

    /**
     * Typewriter effect for situation text (faster, no cursor)
     */
    typewriterEffectForSituation(element, text, callback) {
        let index = 0;
        const type = () => {
            if (index < text.length) {
                element.textContent = text.substring(0, index + 1);
                index++;
                this.scrollToBottom();
                
                // Faster typing for situation
                setTimeout(type, this.typewriterSpeed * 0.5);
            } else {
                element.textContent = text;
                this.scrollToBottom();
                // Small delay before starting dialogue
                setTimeout(callback, 200);
            }
        };

        setTimeout(type, 50);
    }

    /**
     * Typewriter effect implementation
     */
    typewriterEffect(element, text, callback = null) {
        const cursor = document.createElement('span');
        cursor.className = 'typewriter-cursor';
        cursor.textContent = '|';
        element.appendChild(cursor);

        let index = 0;
        const type = () => {
            if (index < text.length) {
                cursor.remove();
                element.textContent = text.substring(0, index + 1);
                element.appendChild(cursor);
                
                index++;
                this.scrollToBottom();
                
                // Variable speed based on character
                let delay = this.typewriterSpeed;
                const char = text[index - 1];
                if ('.!?'.includes(char)) delay *= 4;
                else if (',;:'.includes(char)) delay *= 2;
                else if (char === ' ') delay *= 0.3;
                else if (char === '\n') delay *= 2;
                
                setTimeout(type, delay);
            } else {
                cursor.remove();
                element.innerHTML = this.escapeHtml(text);
                this.scrollToBottom();
                
                // Call callback if provided
                if (callback) {
                    setTimeout(callback, 200);
                }
            }
        };

        setTimeout(type, 100);
    }

    /**
     * Set input state
     */
    setInputState(enabled) {
        if (this.messageInput) this.messageInput.disabled = !enabled;
        if (this.sendButton) this.sendButton.disabled = !enabled;
        if (enabled && this.messageInput) this.messageInput.focus();
    }

    /**
     * Update status indicator
     */
    updateStatus(status, text) {
        if (this.statusDot) this.statusDot.className = `status-dot ${status}`;
        if (this.statusText) this.statusText.textContent = text;
    }

    /**
     * Handle scroll events for loading older messages when scrolled to top
     */
    handleScroll() {
        if (!this.hasMoreHistory || this.isLoadingHistory) return;
        
        const scrollTop = this.chatMessages.scrollTop;
        const threshold = 50; // Load when within 50px of top
        
        // Check if scrolled to top
        if (scrollTop <= threshold) {
            console.log(`🔄 Scrolled to top (${scrollTop}px) - loading older messages automatically`);
            this.loadMoreHistory();
        }
    }

    /**
     * Check if user is scrolled to bottom of chat
     */
    isScrolledToBottom() {
        if (!this.chatMessages) return true;
        
        const scrollTop = this.chatMessages.scrollTop;
        const scrollHeight = this.chatMessages.scrollHeight;
        const clientHeight = this.chatMessages.clientHeight;
        
        // Consider "bottom" if within 50px of actual bottom
        const threshold = 50;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - threshold;
        
        return isAtBottom;
    }

    /**
     * Scroll to bottom of chat with smooth animation
     */
    scrollToBottom(smooth = false) {
        if (this.chatMessages) {
            if (smooth) {
                this.chatMessages.scrollTo({
                    top: this.chatMessages.scrollHeight,
                    behavior: 'smooth'
                });
            } else {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
            console.log('📍 Scrolled to bottom');
        }
    }

    /**
     * Parse message content for situation and dialogue format
     * Handles "[상황] situation_text [대화] dialogue_text" pattern
     */
    parseMessageContent(content) {
        // Check if content contains both [상황] and [대화] labels
        const situationMatch = content.match(/\[상황\]\s*(.*?)(?=\[대화\]|$)/s);
        const dialogueMatch = content.match(/\[대화\]\s*(.*?)$/s);
        
        if (situationMatch && dialogueMatch) {
            return {
                hasSituation: true,
                situation: situationMatch[1].trim(),
                dialogue: dialogueMatch[1].trim()
            };
        }
        
        return {
            hasSituation: false,
            content: content
        };
    }

    /**
     * Escape HTML for safe display
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.addMessage(`✅ ${message}`, 'received');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.addMessage(`❌ ${message}`, 'received', true);
    }

    /**
     * Load chat history from server - loads ONLY latest messages on initial page load
     */
    async loadChatHistory() {
        if (this.chatHistoryLoaded) return;
        
        try {
            console.log('📥 Loading LATEST chat history (initial page load)...');
            console.log('🔧 Configuration:', { 
                userId: this.config.userId, 
                storyId: this.config.storyId 
            });
            
            this.updateStatus('connecting', 'Loading latest messages...');
            
            // Get ONLY latest messages WITHOUT cursor for initial page load
            const response = await this.apiService.getLatestChatHistory(
                this.config.userId, 
                this.config.storyId, 
                20 // Load ONLY last 20 messages
            );
            
            console.log(`📊 Latest messages API response:`, response);
            
            // Extract messages from the response
            const messages = response.messages || [];
            
            if (messages && messages.length > 0) {
                console.log(`✅ Loaded ${messages.length} LATEST messages (no history)`);
                
                // Clear existing messages except welcome message
                this.clearChatForHistory();
                
                // Add messages to UI and conversation history
                messages.forEach(msg => {
                    const messageType = msg.is_user_message ? 'sent' : 'received';
                    // Force scroll for initial load
                    this.addMessage(msg.contents, messageType, false, msg.id, true);
                    
                    // Add to conversation history
                    this.conversationHistory.push({
                        type: msg.is_user_message ? 'user' : 'assistant',
                        message: msg.contents,
                        timestamp: msg.created_at,
                        id: msg.id
                    });
                });
                
                // ALWAYS scroll to bottom after loading latest messages
                setTimeout(() => {
                    this.scrollToBottom();
                    console.log('📍 FORCED scroll to bottom after loading latest messages');
                }, 150);
                
                this.showSuccess(`Loaded ${messages.length} latest messages`);
                
                // Set cursor for pagination (oldest message ID for loading more)
                this.nextCursor = response.next_cursor;
                this.hasMoreHistory = response.has_more || messages.length >= 20; // Assume more if we got full batch
                
                console.log(`🔄 Cursor for older messages: ${this.nextCursor}`);
                console.log(`📊 Has more history: ${this.hasMoreHistory}`);
                
                // Hide load more button initially - will show when scrolling up
                if (this.loadMoreContainer) {
                    this.loadMoreContainer.style.display = 'none';
                }
            } else {
                console.log('ℹ️ No chat history found');
            }
            
            this.chatHistoryLoaded = true;
            this.updateStatus('connected', 'Connected');
            
        } catch (error) {
            console.error('❌ Failed to load chat history:', error);
            this.updateStatus('error', 'Failed to load history');
            this.showError(`Failed to load chat history: ${error.message}`);
        }
    }

    /**
     * Check if there are more messages to load using cursor
     * This method is no longer needed since we get has_more from the main response
     */
    async checkForMoreHistory() {
        // This method is kept for compatibility but not used
        // The has_more flag comes directly from the API response
        return;
    }

    /**
     * Load more chat history using cursor-based pagination
     */
    async loadMoreHistory() {
        if (!this.hasMoreHistory || !this.nextCursor || this.isLoadingHistory) return;
        
        try {
            this.isLoadingHistory = true;
            
            // Show loading indicators
            if (this.loadMoreBtn) {
                this.loadMoreBtn.disabled = true;
                this.loadMoreBtn.textContent = 'Loading...';
            }
            
            if (this.scrollLoadingIndicator) {
                this.scrollLoadingIndicator.style.display = 'block';
            }
            
            // Store current scroll position to maintain it after loading
            const scrollHeight = this.chatMessages.scrollHeight;
            const scrollTop = this.chatMessages.scrollTop;
            
            console.log(`📥 Loading more messages with cursor: ${this.nextCursor}`);
            
            const response = await this.apiService.getChatHistory(
                this.config.userId,
                this.config.storyId,
                20, // Load 20 more messages
                this.nextCursor
            );
            
            console.log(`📊 API Response:`, {
                messages: response.messages?.length || 0,
                has_more: response.has_more,
                next_cursor: response.next_cursor
            });
            
            if (response.messages && response.messages.length > 0) {
                // Insert messages at the beginning (after scroll indicator and welcome message)
                const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
                const insertAfter = welcomeMessage || this.chatMessages.firstChild;
                
                // Messages are already in chronological order (oldest first)
                response.messages.forEach(msg => {
                    const messageDiv = this.createMessageElement(
                        msg.contents, 
                        msg.is_user_message ? 'sent' : 'received',
                        false,
                        msg.id // Pass the message ID
                    );
                    
                    if (insertAfter && insertAfter.nextSibling) {
                        this.chatMessages.insertBefore(messageDiv, insertAfter.nextSibling);
                    } else {
                        this.chatMessages.appendChild(messageDiv);
                    }
                    
                    // Add to conversation history at the beginning
                    this.conversationHistory.unshift({
                        type: msg.is_user_message ? 'user' : 'assistant',
                        message: msg.contents,
                        timestamp: msg.created_at,
                        id: msg.id
                    });
                });
                
                // Maintain scroll position
                const newScrollHeight = this.chatMessages.scrollHeight;
                const heightDifference = newScrollHeight - scrollHeight;
                this.chatMessages.scrollTop = scrollTop + heightDifference;
                
                // Update cursor for next pagination
                this.nextCursor = response.next_cursor;
                this.hasMoreHistory = response.has_more;
                
                console.log(`✅ Loaded ${response.messages.length} more messages`);
                console.log(`🔄 Next cursor: ${this.nextCursor}, Has more: ${this.hasMoreHistory}`);
            }
            
            // Hide load more button if no more messages
            if (!this.hasMoreHistory && this.loadMoreContainer) {
                this.loadMoreContainer.style.display = 'none';
            }
            
        } catch (error) {
            console.error('❌ Failed to load more history:', error);
            this.showError('Failed to load more messages');
        } finally {
            this.isLoadingHistory = false;
            
            // Hide loading indicators
            if (this.loadMoreBtn) {
                this.loadMoreBtn.disabled = false;
                this.loadMoreBtn.textContent = 'Load More Messages';
            }
            
            if (this.scrollLoadingIndicator) {
                this.scrollLoadingIndicator.style.display = 'none';
            }
        }
    }

    /**
     * Create message element without adding to DOM
     */
    createMessageElement(content, type, isError = false, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (isError) {
            messageDiv.style.backgroundColor = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.border = '1px solid #f5c6cb';
        }

        const timeString = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        // Parse content for situation/dialogue format
        const parsed = this.parseMessageContent(content);
        
        let messageContentHtml;
        if (parsed.hasSituation) {
            messageContentHtml = `
                <div class="message-situation-content">${this.escapeHtml(parsed.situation)}</div>
                <div class="message-dialogue-content">${this.escapeHtml(parsed.dialogue)}</div>
            `;
        } else {
            messageContentHtml = this.escapeHtml(parsed.content);
        }

        // Create message ID display if available
        const messageIdHtml = messageId ? `<div class="message-id">ID: ${messageId}</div>` : '';

        messageDiv.innerHTML = `
            <div class="message-content">${messageContentHtml}</div>
            <div class="message-footer">
                <div class="message-time">${timeString}</div>
                ${messageIdHtml}
            </div>
        `;

        return messageDiv;
    }

    /**
     * Clear chat messages but keep welcome message
     */
    clearChatForHistory() {
        if (this.chatMessages) {
            const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
            messages.forEach(msg => msg.remove());
        }
        this.conversationHistory = [];
    }

    /**
     * Reload chat history when config changes - loads latest messages and scrolls to bottom
     */
    async reloadChatHistory() {
        console.log('🔄 Reloading chat history due to config change...');
        
        this.chatHistoryLoaded = false;
        this.nextCursor = null;
        this.prevCursor = null;
        this.hasMoreHistory = false;
        this.isLoadingHistory = false;
        this.conversationHistory = [];
        
        // Clear existing messages
        this.clearChatForHistory();
        
        if (this.loadMoreContainer) {
            this.loadMoreContainer.style.display = 'none';
        }
        
        // Load latest messages for new configuration
        await this.loadChatHistory();
        
        // Ensure scroll to bottom after reload
        setTimeout(() => {
            this.scrollToBottom();
            console.log('📍 Auto-scrolled to bottom after config reload');
        }, 200);
    }

    /**
     * Clear chat history
     */
    clearChat() {
        this.conversationHistory = [];
        if (this.chatMessages) {
            // Keep welcome message, remove others
            const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
            messages.forEach(msg => msg.remove());
        }
        this.chatHistoryLoaded = false;
        this.nextCursor = null;
        this.prevCursor = null;
        this.hasMoreHistory = false;
        if (this.loadMoreContainer) {
            this.loadMoreContainer.style.display = 'none';
        }
        this.showSuccess('Chat cleared');
    }

    /**
     * Export chat history
     */
    exportChat() {
        const data = {
            timestamp: new Date().toISOString(),
            config: this.config,
            history: this.conversationHistory
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `matehub-chat-${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showSuccess('Chat exported');
    }
}

// Export for global use
window.ChatClient = ChatClient;
