class AutoAuth {
    constructor() {
        this.apiBase = 'http://localhost:8000';
    }

    async ensureAuth() {
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
            await this.getAnonymousToken();
        }
        
        // Check if user just completed Kakao login
        this.checkLoginStatus();
    }

    checkLoginStatus() {
        const isAnonymous = localStorage.getItem('is_anonymous');
        if (isAnonymous === 'false') {
            // User just logged in, trigger UI update
            setTimeout(() => {
                if (window.chatApp && window.chatApp.loadUserInfo) {
                    window.chatApp.loadUserInfo();
                }
            }, 100);
        }
    }

    async getAnonymousToken() {
        try {
            const refreshToken = localStorage.getItem('refresh_token') || '';
            
            const response = await fetch(`${this.apiBase}/auth/anonymous-token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const tokens = await response.json();
                localStorage.setItem('access_token', tokens.access_token);
                localStorage.setItem('refresh_token', tokens.refresh_token);
            }
        } catch (error) {
            console.error('Auto auth failed:', error);
        }
    }

    async startKakaoLogin() {
        try {
            const response = await fetch(`${this.apiBase}/auth/kakao/login`);
            const data = await response.json();
            
            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                alert('카카오 로그인 URL을 가져올 수 없습니다.');
            }
        } catch (error) {
            console.error('Kakao login failed:', error);
            alert('카카오 로그인 중 오류가 발생했습니다.');
        }
    }
}

// 페이지 로드 시 자동 인증
window.autoAuth = new AutoAuth();
window.autoAuth.ensureAuth();
