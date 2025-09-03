class KakaoAuth {
    constructor(clientId, redirectUri) {
        this.clientId = clientId;
        this.redirectUri = redirectUri;
    }
    
    login() {
        const kakaoAuthUrl = `https://kauth.kakao.com/oauth/authorize?client_id=${this.clientId}&redirect_uri=${encodeURIComponent(this.redirectUri)}&response_type=code`;
        
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
