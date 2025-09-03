class AuthService {
    constructor() {
        this.apiBase = 'http://localhost:8000';
    }

    showStatus(message, isError = false) {
        const status = document.getElementById('status');
        status.textContent = message;
        status.className = `status ${isError ? 'error' : 'success'}`;
        status.style.display = 'block';
        
        setTimeout(() => {
            status.style.display = 'none';
        }, 3000);
    }

    saveTokens(tokens) {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        localStorage.setItem('user_type', tokens.user_type);
    }

    async kakaoLogin() {
        try {
            this.showStatus('카카오 로그인 중...');
            
            // 카카오 로그인 URL 요청
            const response = await fetch(`${this.apiBase}/auth/kakao/login`);
            if (!response.ok) {
                throw new Error('카카오 로그인 URL 요청 실패');
            }
            
            const data = await response.json();
            
            // 카카오 로그인 페이지로 리다이렉트
            window.location.href = data.auth_url;
            
        } catch (error) {
            this.showStatus('카카오 로그인 실패: ' + error.message, true);
        }
    }

    async anonymousLogin() {
        try {
            this.showStatus('익명 로그인 중...');
            
            // 기존 refresh token 확인
            let refreshToken = localStorage.getItem('refresh_token') || '';
            
            const response = await fetch(`${this.apiBase}/auth/anonymous-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (!response.ok) {
                throw new Error('익명 로그인 실패');
            }

            const tokens = await response.json();
            this.saveTokens(tokens);
            this.showStatus('익명 로그인 성공!');
            
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);

        } catch (error) {
            this.showStatus('익명 로그인 실패: ' + error.message, true);
        }
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    const authService = new AuthService();
    
    document.getElementById('kakaoLogin').addEventListener('click', () => {
        authService.kakaoLogin();
    });
    
    document.getElementById('anonymousLogin').addEventListener('click', () => {
        authService.anonymousLogin();
    });
    
    document.getElementById('directChat').addEventListener('click', () => {
        window.location.href = 'index.html';
    });
    
    // 이미 로그인된 경우 채팅 페이지로 이동
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
        window.location.href = 'index.html';
    }
});
