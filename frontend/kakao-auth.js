class KakaoAuth {
    constructor(clientId, redirectUri) {
        this.clientId = clientId;
        this.redirectUri = redirectUri;
    }
    
    async login() {
        try {
            // 서버에서 카카오 인증 URL 받아오기
            const response = await fetch('http://localhost:8000/auth/kakao/login');
            const data = await response.json();
            
            if (!response.ok || !data.auth_url) {
                throw new Error('인증 URL을 받아올 수 없습니다.');
            }
            
            const kakaoAuthUrl = data.auth_url;
            
            // 팝업으로 카카오 로그인 창 열기
            const popup = window.open(kakaoAuthUrl, 'kakaoLogin', 'width=500,height=600');
            
            return new Promise((resolve, reject) => {
                // 메시지 리스너 등록
                const messageHandler = (event) => {
                    if (event.origin !== 'http://localhost:3000') return;
                    
                    if (event.data.type === 'KAKAO_LOGIN_SUCCESS') {
                        window.removeEventListener('message', messageHandler);
                        resolve(event.data.data);
                    } else if (event.data.type === 'KAKAO_LOGIN_ERROR') {
                        window.removeEventListener('message', messageHandler);
                        reject(new Error(event.data.error));
                    }
                };
                
                window.addEventListener('message', messageHandler);
                
                // 팝업이 닫혔는지 체크
                const checkClosed = setInterval(() => {
                    if (popup.closed) {
                        clearInterval(checkClosed);
                        window.removeEventListener('message', messageHandler);
                        reject(new Error('로그인이 취소되었습니다.'));
                    }
                }, 1000);
            });
        } catch (error) {
            throw new Error(`카카오 로그인 초기화 실패: ${error.message}`);
        }
    }
    
    // 백엔드 콜백에서 프론트엔드로 리다이렉트하는 URL 생성
    static createCallbackBridgeUrl(accessToken, refreshToken, kakaoId, isNewUser) {
        const params = new URLSearchParams({
            access_token: accessToken,
            refresh_token: refreshToken,
            kakao_id: kakaoId,
            is_new_user: isNewUser
        });
        return `http://localhost:3000/callback-bridge.html?${params.toString()}`;
    }
}
