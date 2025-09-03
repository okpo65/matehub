class ChatApp {
    constructor() {
        this.apiService = new ApiService();
        this.storyId = null;
        this.isLoading = false;
        
        this.init();
    }

    async init() {
        // 자동 인증 완료 대기
        await window.autoAuth.ensureAuth();
        
        this.setupEventListeners();
        await this.loadUserInfo();
        await this.loadStories();
    }

    setupEventListeners() {
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        const logoutBtn = document.getElementById('logoutBtn');
        const kakaoLoginBtn = document.getElementById('kakaoLoginBtn');

        sendBtn.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        logoutBtn.addEventListener('click', () => this.apiService.logout());
        kakaoLoginBtn.addEventListener('click', () => window.autoAuth.startKakaoLogin());
    }

    async loadUserInfo() {
        try {
            const user = await this.apiService.getCurrentUser();
            const kakaoLoginBtn = document.getElementById('kakaoLoginBtn');
            
            if (user.is_anonymous) {
                document.getElementById('userInfo').textContent = '익명 사용자';
                kakaoLoginBtn.style.display = 'inline-block';
            } else {
                document.getElementById('userInfo').textContent = 
                    user.kakao_id ? `카카오 사용자 (${user.kakao_id})` : `사용자 (${user.name || user.id})`;
                kakaoLoginBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('사용자 정보 로드 실패:', error);
            document.getElementById('userInfo').textContent = '익명 사용자';
            document.getElementById('kakaoLoginBtn').style.display = 'inline-block';
        }
    }

    async loadStories() {
        try {
            const storyList = document.getElementById('storyList');
            storyList.innerHTML = '<div class="status">스토리를 불러오는 중...</div>';
            
            const stories = await this.apiService.getStories();
            
            if (stories.stories && stories.stories.length > 0) {
                storyList.innerHTML = '';
                stories.stories.forEach(story => {
                    const storyItem = document.createElement('div');
                    storyItem.className = 'story-item';
                    storyItem.dataset.storyId = story.id;
                    storyItem.innerHTML = `
                        <div class="story-title">${story.storyline}</div>
                        <div class="story-character">${story.character?.description || '캐릭터 정보 없음!'}</div>
                    `;
                    
                    storyItem.addEventListener('click', () => this.selectStory(story));
                    storyList.appendChild(storyItem);
                });
            } else {
                storyList.innerHTML = '<div class="status">사용 가능한 스토리가 없습니다.</div>';
            }
        } catch (error) {
            console.error('스토리 로드 실패:', error);
            document.getElementById('storyList').innerHTML = '<div class="status">스토리를 불러올 수 없습니다.</div>';
        }
    }

    async selectStory(story) {
        // 이전 선택 해제
        document.querySelectorAll('.story-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 새 선택 활성화
        document.querySelector(`[data-story-id="${story.id}"]`).classList.add('active');
        
        this.storyId = story.id;
        document.getElementById('currentStoryTitle').textContent = story.title;
        
        // 입력 활성화
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        
        // 채팅 기록 로드
        await this.loadChatHistory();
    }

    async loadChatHistory() {
        if (!this.storyId) return;
        
        try {
            this.setStatus('채팅 기록을 불러오는 중...');
            const history = await this.apiService.getLatestChatHistory(this.storyId, 20);
            
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = '';
            
            if (history.messages && history.messages.length > 0) {
                history.messages.forEach(msg => {
                    this.addMessage(msg.contents, msg.is_user_message ? 'sent' : 'received');
                });
                this.setStatus('');
            } else {
                this.setStatus('새로운 대화를 시작해보세요!');
            }
            
            this.scrollToBottom();
        } catch (error) {
            console.error('채팅 기록 로드 실패:', error);
            this.setStatus('채팅 기록을 불러올 수 없습니다.');
        }
    }

    async sendMessage() {
        if (!this.storyId) {
            this.setStatus('먼저 스토리를 선택해주세요.');
            return;
        }
        
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        console.log('Message to send:', message); // 디버깅용
        
        if (!message || this.isLoading) return;

        this.isLoading = true;
        this.updateSendButton(false);
        
        // 사용자 메시지 추가
        this.addMessage(message, 'sent');
        messageInput.value = '';
        this.scrollToBottom();
        
        this.setStatus('AI가 응답하는 중...');

        try {
            const response = await this.apiService.sendMessage(this.storyId, message);
            
            if (response.story_chat_history_id) {
                // 별도 함수에서 polling 시작
                this.startPolling(response.story_chat_history_id);
            } else {
                this.handleSendError('메시지 전송에 실패했습니다.');
            }
        } catch (error) {
            console.error('메시지 전송 실패:', error);
            this.handleSendError('메시지 전송에 실패했습니다.');
        }
    }

    startPolling(messageId) {
        let attempts = 0;
        const maxAttempts = 30;
        
        const poll = async () => {
            try {
                attempts++;
                const status = await this.apiService.getSendMessageStatus(messageId);
                console.log('Status:', status);
                if (status.status === 'completed') {
                    const messageResponse = await this.apiService.getMessageResponse(messageId);
                    this.handlePollingSuccess(messageResponse.contents);
                    return;
                }
                
                if (status.status === 'failed') {
                    this.handleSendError('AI 응답 생성에 실패했습니다.');
                    return;
                }
                
                if (attempts >= maxAttempts) {
                    this.handleSendError('응답 시간이 초과되었습니다.');
                    return;
                }
                
                // 1초 후 재시도
                setTimeout(poll, 1000);
                
            } catch (error) {
                console.error('상태 확인 실패:', error);
                if (attempts >= maxAttempts) {
                    this.handleSendError('응답을 받을 수 없습니다.');
                } else {
                    setTimeout(poll, 1000);
                }
            }
        };
        
        poll();
    }

    handlePollingSuccess(aiResponse) {
        this.addMessage(aiResponse, 'received');
        this.setStatus('');
        this.isLoading = false;
        this.updateSendButton(true);
        this.scrollToBottom();
    }

    handleSendError(errorMessage) {
        this.addMessage(errorMessage, 'received');
        this.setStatus('');
        this.isLoading = false;
        this.updateSendButton(true);
        this.scrollToBottom();
    }

    addMessage(text, type) {
        const messagesContainer = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
    }

    setStatus(text) {
        document.getElementById('status').textContent = text;
    }

    updateSendButton(enabled) {
        const sendBtn = document.getElementById('sendBtn');
        if (this.storyId) {
            sendBtn.disabled = !enabled;
            sendBtn.textContent = enabled ? '전송' : '전송 중...';
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
