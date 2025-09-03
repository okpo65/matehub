class ApiService {
    constructor() {
        this.baseURL = 'http://localhost:8000';
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;

        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const tokens = await response.json();
                localStorage.setItem('access_token', tokens.access_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        return false;
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });
            
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // 토큰 갱신 후 재시도
                    const newHeaders = {
                        'Content-Type': 'application/json',
                        ...this.getAuthHeaders(),
                        ...options.headers
                    };
                    return fetch(url, { ...options, headers: newHeaders });
                } else {
                    // 토큰 갱신 실패 시 로그인 페이지로
                    window.location.href = 'auth.html';
                    return;
                }
            }
            
            return response;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // 채팅 관련 API
    async sendMessage(storyId, message) {
        const requestData = {
            story_id: storyId,
            model: "gemini-2.0-flash-lite",
            message: message
        };
        
        console.log('Sending message:', requestData); // 디버깅용
        
        const response = await this.apiCall('/llm/chat', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        return response.json();
    }

    async getSendMessageStatus(storyChatHistoryId) {
        const response = await this.apiCall(`/llm/chat_history_status/${storyChatHistoryId}`);
        return response.json();
    }

    async getMessageResponse(storyChatHistoryId) {
        const response = await this.apiCall(`/llm/chat_history/${storyChatHistoryId}`);
        return response.json();
    }

    async getChatHistory(storyId, limit = 20, cursor = null) {
        const params = new URLSearchParams({
            story_id: storyId,
            limit: limit
        });
        
        if (cursor) {
            params.append('cursor', cursor);
        }

        const response = await this.apiCall(`/chat/history?${params}`);
        return response.json();
    }

    async getLatestChatHistory(storyId, limit = 20) {
        return this.getChatHistory(storyId, limit);
    }

    // 캐릭터 관련 API
    async getCharacters() {
        const response = await this.apiCall('/characters/');
        return response.json();
    }

    // 스토리 관련 API
    async getStories() {
        const response = await this.apiCall('/stories/');
        return response.json();
    }

    async getCharacterStories(characterId) {
        const response = await this.apiCall(`/stories/character/${characterId}`);
        return response.json();
    }

    // 사용자 정보 API
    async getCurrentUser() {
        const response = await this.apiCall('/auth/me');
        return response.json();
    }

    async getKakaoAuthUrl() {
        const response = await this.apiCall('/auth/kakao/login');
        return response.json();
    }

    // 로그아웃
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = 'auth.html';
    }
}
